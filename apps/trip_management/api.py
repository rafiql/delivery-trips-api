from datetime import datetime, date
import polyline, geojson
from django.conf import settings
from django.db import transaction
from django.core.management import call_command

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, AuthenticationFailed, NotAcceptable
from apps.user.permission import IsSuperUser
from apps.user.config import ROLE_DICT
from apps.base.map_helpers import auto_complete_dingi, get_fastest_route, auto_complete_google, get_address
from apps.trip_management.helpers import (get_invoice_data, get_driver_data, get_vehicle_data, get_warehouse_data, 
            get_tripinfo_data, get_destionation_data, trip_sms_sender, get_deliveryman_data)
from apps.trip_management.models import Invoice, Driver, DeliveryMan, TripDeliveryMan, Vehicle, WareHouse, TripInfo, Destinations
from apps.trip_management.config import DELIVERY_STATUS, TRIP_STATUS
from apps.trip_management.geofence import in_fence



@api_view(['POST'])
@permission_classes([IsSuperUser])
def trip_scheduler_sorter(request):
    data = request.data

    sorted_data = []
    vehicle_driver_set = {}
    deliverymans_data = []

    for item in data:
        driver = get_driver_data(Driver.objects.get(pk=item.pop('driver_id')))
        vehicle = get_vehicle_data(Vehicle.objects.get(pk=item.pop('vehicle_id')))
        warehouse = get_warehouse_data(WareHouse.objects.get(pk=item.pop('warehouse_id')))
        deliverymans = item.pop('deliverymans', None)
        if deliverymans is not None:
            for man in deliverymans:
                deliverymans_data.append(get_deliveryman_data(DeliveryMan.objects.get(pk=man)))
        vehicle.pop('driver')
        if len(sorted_data)==0:
            sorted_data.append({
                'vehicle' : vehicle,
                'driver' : driver,
                'deliverymans': deliverymans_data if deliverymans_data else [] ,
                'trip_date' : item.pop('trip_date'),
                'warehouse' : warehouse,
                'invoices' : [{**item}]
            })
            vehicle_driver_set[vehicle['id']] = driver['id']

        elif vehicle['id'] in list(vehicle_driver_set.keys()):
            if driver['id'] == vehicle_driver_set[vehicle['id']]:
                # sorted_data[vehicle]={invoice_id:{**item}}
                data_dict = next(filter(lambda x: (x['vehicle']==vehicle and  x['driver']==driver), sorted_data))
                sorted_data.remove(data_dict)
                data_dict['invoices'].append({**item})
                sorted_data.append(data_dict) 
            else:
                raise ValidationError(vehicle['title'] + " assigned with multiple driver", code=400)
        else:
            sorted_data.append({
                'vehicle' : vehicle,
                'driver' : driver,
                'deliverymans': deliverymans_data if deliverymans_data else [] ,
                'trip_date' : item.pop('trip_date'),
                'warehouse' : warehouse,
                'invoices' : [{**item}]
            })
            vehicle_driver_set[vehicle['id']] = driver['id']
    
    return Response(sorted_data)



@api_view(['GET'])
@permission_classes([IsSuperUser])
def invoice_by_date(request):
    date = request.GET.get('date', None)

    if date is not None:
        date = datetime.strptime(date, settings.DATE_INPUT_FORMATS[1])
    else:
        raise ValidationError('No date provided!!!')

    # invoice_qs = Invoice.objects.filter(delivery_status=DELIVERY_STATUS['Pending'], estimated_delivery_date__lte = date)
    invoice_qs = Invoice.objects.filter(delivery_status__in=[1,5], estimated_delivery_date__lte = date)

    invoices = []
    if invoice_qs.exists():
        for invoice in invoice_qs:
            invoice_data = get_invoice_data(invoice)
            # location = auto_complete_dingi(invoice.delivery_address)['result'][0]['location']
            # location.reverse()
            # invoice_data.update({'location': location})
            invoices.append(invoice_data)
    else:
        raise ValidationError('No Invoice available for delivery.')

    return Response(invoices)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def trip_scheduler(request):
    data = request.data
    results = []
    for trip in data:
        trip_instance = None
        ins = {}
        with transaction.atomic():
            trip_instance = TripInfo(
                trip_date = datetime.strptime(trip.get('date'), settings.DATE_INPUT_FORMATS[1]),
                driver_id = trip.get('driver_id'),
                vehicle_id = trip.get('vehicle_id'),
                warehouse_id = trip.get('warehouse_id'),
                trip_status = TRIP_STATUS['Scheduled']
                )
            trip_instance.save()
            deliverymans = list(trip.get('deliverymans', None))
            if deliverymans is not None:
                # ins['trip_deliveryman'] = []
                for man in deliverymans:
                    trip_deliveryman = TripDeliveryMan(trip_info=trip_instance, deliveryman_id=man)
                    trip_deliveryman.save()
                    # ins['trip_deliveryman'].append(get_trip_deliveryman(trip_deliveryman))
            ins['trip_instance'] = get_tripinfo_data(trip_instance)
            if trip_instance is not None:
                ins['destinations'] = []
                for invoice in trip['invoices']:
                    destination_instance = Destinations(
                        trip_info = trip_instance,
                        invoice_id = invoice.get('id'),
                        sequence = invoice.get('sequence'),
                    )
                    instance = Invoice.objects.filter(pk=invoice.get('id'))
                    instance.update(
                        delivery_status=DELIVERY_STATUS['Scheduled'],
                        lon = invoice.get('location')[0],
                        lat = invoice.get('location')[1]
                        )
                    instance = instance.first()
                    sms_status = trip_sms_sender(instance.customer_phone_no, instance.invoice_id, 
                                    trip_instance.driver.name, trip_instance.driver.phone_no)
                    destination_instance.sms_status = sms_status.status_code
                    destination_instance.save()
                    ins['destinations'].append(get_destionation_data(destination_instance))
        results.append(ins)
    
    return Response(results)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scheduled_trip(request):
    user = request.user
    get_date = request.GET.get('date', None)
    if get_date is None:
        get_date = datetime.fromordinal(date.today().toordinal())
    else:
        get_date = datetime.strptime(get_date, settings.DATE_INPUT_FORMATS[1])

    filter_arg = {'trip_date': get_date}
    vehicle_id = request.GET.get('vehicle_id', None)
    if vehicle_id is not None:
        filter_arg.update({'vehicle_id':vehicle_id})
    trips = TripInfo.objects.filter(**filter_arg)

    results = []

    if trips.exists():
        for trip in trips:
            ins = {}
            destinations = Destinations.objects.filter(trip_info=trip).order_by('sequence')
            if user.role == ROLE_DICT['SalesManager']:
                destinations = destinations.filter(invoice__sales_point=user.salespoint)
            if destinations.exists():
                ins['destinations'] = []
                for destination in destinations:
                    ins['destinations'].append(get_destionation_data(destination))
            else:continue
            ins['trip_instance'] = get_tripinfo_data(trip)
            results.append(ins)
    
    return Response(results)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def trip_deletion(request):
    trip_id = request.GET.get('trip_id', None)

    if trip_id is not None:
        destinations = Destinations.objects.filter(trip_info_id=trip_id)
        for destiny in destinations:
            invoice=destiny.invoice
            invoice.delivery_status=DELIVERY_STATUS['Pending']
            invoice.save()
        TripInfo.objects.filter(pk=trip_id).delete()
        return Response(["Deleted Successfully"])


@api_view(['PUT', 'PATCH', 'POST'])
@permission_classes([IsSuperUser])
def destination_mod(request):  
    if request.method == 'PUT':
        destination_id = request.data.get('destination_id', None)
        if destination_id is None:
            return Response({"msg":"destination_id Required"}, status=400)
        else:
            destination = Destinations.objects.get(pk=destination_id)
            destinations = Destinations.objects.filter(trip_info=destination.trip_info, \
                                sequence__gt=destination.sequence).order_by('sequence')
            if destinations.exists():
                next_destination = destinations[0]
                next_destination.route_history = destination.route_history
                next_destination.invoice.delivery_status = destination.invoice.delivery_status
                next_destination.invoice.save()
                next_destination.save()
                for destiny in destinations:
                    destiny.sequence -= 1
                    destiny.save()
            else:
                destination.trip_info.return_route_history = destination.route_history+destination.trip_info.return_route_history
                if destination.trip_info.return_route_history:
                    if in_fence({'lat':destination.trip_info.warehouse.lat, 'lon':destination.trip_info.warehouse.lon}, \
                            destination.trip_info.return_route_history[-1]):
                        destination.trip_info.trip_end_time = datetime.strptime(destination.trip_info.return_route_history[-1]['time'], settings.DATE_INPUT_FORMATS[2])
                        destination.trip_info.trip_status = TRIP_STATUS['Complete']
                destination.trip_info.save()
            invoice=destination.invoice
            invoice.delivery_status=DELIVERY_STATUS['Pending']
            invoice.save()
            destination.delete()
            return Response({"msg":"Deleted Successfully"})
    elif request.method == 'POST':
        trip_id = request.data.get('trip_id', None)
        if trip_id is None:
            return Response({"msg":"trip_id Required"}, status=400)
        invoice_id = request.data.get('invoice_id', None)
        if invoice_id is None:
            return Response({"msg":"invoice_id Required"}, status=400)
        sequence = request.data.get('sequence', None)
        if sequence is None:
            return Response({"msg":"sequence Required"}, status=400)
        trip_instance = TripInfo.objects.get(pk=trip_id)
        destinations = Destinations.objects.only('id', 'trip_info', 'sequence')\
                        .filter(trip_info=trip_instance, sequence__gte=sequence).order_by('sequence')
        if destinations.exists():
            if destinations[0].invoice.delivery_status==DELIVERY_STATUS['OnDelivery']:
                raise NotAcceptable(detail="DELIVERY ONGOING")
            for destiny in destinations:
                destiny.sequence += 1
                destiny.save()
        destination_instance = Destinations(
            trip_info = trip_instance,
            invoice_id = invoice_id,
            sequence = sequence,
        )
        instance = Invoice.objects.get(pk=invoice_id)
        instance.delivery_status=DELIVERY_STATUS['Scheduled']
        if request.data.get('location', None) is not None:
            instance.lon = request.data.get('location')[0],
            instance.lat = request.data.get('location')[1]
        instance.save()
        sms_status = trip_sms_sender(instance.customer_phone_no, instance.invoice_id, 
                        trip_instance.driver.name, trip_instance.driver.phone_no)
        destination_instance.sms_status = sms_status.status_code
        destination_instance.save()
        return Response({"msg":"Added Successfully"})
    elif request.method == 'PATCH':
        destination_id = request.data.get('destination_id', None)
        if destination_id is None:
            return Response({"msg":"destination_id Required"}, status=400)
        sequence = request.data.get('sequence', None)
        if sequence is None:
            return Response({"msg":"sequence Required"}, status=400)
        destination = Destinations.objects.get(pk=destination_id)
        alt_destination = Destinations.objects.get(trip_info=destination.trip_info, sequence=sequence)
        alt_destination.sequence = destination.sequence
        alt_destination.route_history = destination.route_history
        alt_destination.invoice.delivery_status = destination.invoice.delivery_status
        alt_destination.invoice.save()
        alt_destination.save()
        destination.sequence = sequence
        destination.route_history = []
        destination.invoice.delivery_status = DELIVERY_STATUS['Scheduled']
        destination.invoice.save()
        destination.save()
        return Response({"msg":"Altered Successfully"})


@api_view(['GET'])
@permission_classes([AllowAny])
def tracker(request):
    result = {}
    auth = request.headers.get("authorization", None)
    # route_fields=['geometry', 'duration', 'distance']
    if auth:
        user = request.user
        if (user and user.is_authenticated):
            trip_id = request.GET.get('trip_id')
            trip = TripInfo.objects.get(pk=trip_id)
            vehicle_location = trip.vehicle_location
            if vehicle_location is None:
                raise NotAcceptable(detail='Trip has not been started yet! Try after few mintues.')
            warehouse_location = [trip.warehouse.lon,trip.warehouse.lat]
            result['trip_info'] = get_tripinfo_data(trip)
            result['vehicle_location']=vehicle_location
            destinations_qs = Destinations.objects.filter(trip_info=trip)
            if user.role == ROLE_DICT['SalesManager']:
                destinations_qs = destinations_qs.filter(invoice__sales_point=user.salespoint)
                if not destinations_qs.exists():
                    raise NotAcceptable(detail='Trip has no delivery for your clients.')
            result['destinations'] = []
            for destiny in destinations_qs:
                destination = {}
                data = get_destionation_data(destiny)
                destination['data'] = data
                if data['sequence'] == 1:
                    route = get_fastest_route(warehouse_location, data['location'])
                else:
                    source_data = destinations_qs.get(sequence = data['sequence']-1)
                    source = [source_data.invoice.lon, source_data.invoice.lat]
                    route = get_fastest_route(source, data['location'])
                # route = { x: route["routes"][0][x] for x in route_fields }
                route = route.get("routes", None)
                if route is not None:
                    route = route[0]
                    route_data = {
                        'geometry' : route.get('geometry', None),
                        'duration' : route.get('duration', None),
                        'distance' : route.get('distance', None),
                    }
                    if route_data['geometry'] is not None:
                        route_data['geometry'] =  polyline.decode(route_data['geometry'], 6)
                        route_data.update(geojson.Feature(geometry=geojson.LineString(route_data['geometry'])))
                    destination['route'] = route_data
                else:
                    destination['route'] = {}
                result['destinations'].append(destination)
        else:
            raise AuthenticationFailed(detail='Invalid credentials!')
    else:
        invoice_id = request.GET.get('invoice_id')
        destination = {}
        invoice = Invoice.objects.get(invoice_id=invoice_id)
        if invoice.delivery_status == DELIVERY_STATUS['Delivered']:
            return Response({'status':'delivered'})
        destination_qs = Destinations.objects.filter(invoice_id=invoice.id, route_distance__isnull=True).order_by('-created_at')
        if not destination_qs.exists():
            raise ValidationError(detail="No tracking info found")
        destination_qs = destination_qs.first()
        trip = destination_qs.trip_info
        result['trip_info'] = get_tripinfo_data(trip)
        vehicle_location = trip.vehicle_location
        if vehicle_location is None:
            raise NotAcceptable(detail='Trip has not been started yet! Try after few mintues.')
        result['vehicle_location']=vehicle_location
        data = get_destionation_data(destination_qs)
        destination['data'] = data
        route = get_fastest_route([vehicle_location["location"]["lon"],vehicle_location["location"]["lat"]] , data['location'])
        # route = { x: route["routes"][0][x] for x in route_fields }
        route = route.get("routes", None)
        if route is not None:
            route = route[0]
            route_data = {
                        'geometry' : route.get('geometry', None),
                        'duration' : route.get('duration', None),
                        'distance' : route.get('distance', None),
                    }
            if route_data['geometry'] is not None:
                route_data['geometry'] =  polyline.decode(route_data['geometry'], 6)
                route_data.update(geojson.Feature(geometry=geojson.LineString(route_data['geometry'])))
            destination['route'] = route_data
        else:
            destination['route'] = {}
        result['destinations']=[destination]

    return Response(result)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def invoice_search(request):
    allowed_fields = ['invoice_id', 'delivery_status']
    for param in request.GET:
        if param not in allowed_fields:
            return Response({'msg': "Invalid Search"})

        obj_qs = Invoice.objects.only('id','invoice_id', 'delivery_status')\
                                .filter(invoice_id__icontains=request.GET.get('invoice_id'),
                                delivery_status__in=[1,5]).values('id', 'invoice_id')

    return Response(list(obj_qs), status=200)
        

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def delivery_count(request):
    return Response({'count':Invoice.objects.only('delivery_status')\
                                .filter(delivery_status=DELIVERY_STATUS['Delivered']).count()})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vehicle_search(request):
    allowed_fields = ['title']
    for param in request.GET:
        if param not in allowed_fields:
            return Response({'msg': "Invalid Search"})

        obj_qs = Vehicle.objects.only('id','title')\
                                .filter(title__icontains=request.GET.get('title')
                                ).values('id', 'title')

    return Response(list(obj_qs), status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def deliveryman_search(request):
    allowed_fields = ['name']
    for param in request.GET:
        if param not in allowed_fields:
            return Response({'msg': "Invalid Search"})

        obj_qs = DeliveryMan.objects.only('id','name')\
                                .filter(name__icontains=request.GET.get('name')
                                ).values('id', 'name')

    return Response(list(obj_qs), status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def address_search(request):
    result = []
    if int(request.GET.get('map', 1)) ==1:
        result = auto_complete_google(request.GET.get('token', None))
    else:
        result = auto_complete_dingi(request.GET.get('token', None))
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def geocode_to_address(request):
    result = []
    map = request.GET.get('map', 1)
    result = get_address(latitude=request.GET.get('lat', None), longitude=request.GET.get('lon', None), provider=int(map))
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def call_get_invoice(request):
    call_command('get_invoices')
