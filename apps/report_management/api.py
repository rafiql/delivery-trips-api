from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.http.response import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.base.helpers import to_dict
from apps.user.permission import IsSuperUser
from apps.trip_management.models import Destinations, TripInfo, TripDeliveryMan
from apps.trip_management.config import TRIP_STATUS
from apps.report_management.models import DutyLogBook, EmployeeReport
from apps.report_management.helper import get_gatepass_data, employee_data_fetch, existing_employee_data_fetch


@api_view(['GET','POST','PUT'])
@permission_classes([IsSuperUser])
def dutyloggerentry(request):
    result = {'dutylog':{}, 'employees':[]}
    if request.method == 'POST':
        data = request.data
        dutylog = data.get('dutylog', None)
        employees = data.get('employees', None)
        dutylog['total_ot_payment'], dutylog['total_tiffin'] , dutylog['total_ot_allowance'], dutylog['total_hotel'] , \
            dutylog['total_allowance'],  dutylog['total_one_day_salary'] = [0,0,0,0,0,0]
        for employee in employees:
            dutylog['total_ot_payment'] += float(employee["ot_payment"])
            dutylog['total_tiffin'] += float(employee["tiffin"])
            dutylog['total_ot_allowance'] += float(employee["ot_allowance"])
            dutylog['total_hotel'] += float(employee["hotel"])
            dutylog['total_allowance'] += float(employee["allowance"])
            dutylog['total_one_day_salary'] += float(employee["one_day_salary"])
        dutylog["total_distance"] = 0
        for index, destination in enumerate(dutylog["destinations"]):
            dutylog["total_distance"] += round(float(destination["distance"]), 2)
            if index == 0:
                destination["start_reading"] = round(float(dutylog.pop("start_reading")), 2)
            else:
                destination["start_reading"] = round(dutylog["destinations"][index-1]["end_reading"],2)
            destination["end_reading"] = round(destination["start_reading"] + destination["distance"],2)
            dutylog["destinations"][index] = destination
        with transaction.atomic():
            logdate = datetime.strptime(dutylog.pop('logdate', None), settings.DATE_INPUT_FORMATS[1])
            dutylog['total_vehicle_cost'] = float(dutylog.get('fuel_cost',0)) + float(dutylog.get('toll_fuel_cost',0)) +  float(dutylog.get('others_fuel_cost',0))
            dutylog['total_delivery_cost'] = dutylog['total_vehicle_cost'] + dutylog['total_ot_payment'] + dutylog['total_tiffin'] \
                                            + dutylog['total_ot_allowance'] + dutylog['total_hotel'] +\
                                            dutylog['total_allowance'] +  dutylog['total_one_day_salary']
            dutylog['dp_percent'] = (dutylog['total_delivery_cost']/dutylog['total_delivery_value_dp'])*100
            dutylog['sp_percent'] = (dutylog['total_delivery_cost']/dutylog['total_delivery_value_sp'])*100
            dutylog['cost_per_kilo'] = float(dutylog['total_delivery_cost']/dutylog["total_distance"])
            vehicle_id = int(dutylog.pop('vehicle_id'))
            dutylog, _ = DutyLogBook.objects.update_or_create(vehicle_id=vehicle_id, logdate=logdate, defaults=dutylog)
            # dutylog_ins = DutyLogBook.objects.filter(vehicle_id=dutylog['vehicle_id'], logdate=dutylog['logdate'])
            # if dutylog_ins.exists():
            #     dutylog_ins.update(**dutylog)
            # else:
            #     dutylog_ins = DutyLogBook.objects.create(**dutylog)
            result['dutylog'] = to_dict(dutylog)
            for employee in employees:
                instance = {} # 
                duty_log_book_id = dutylog.id
                if employee.get("designation") == "Driver":
                    driver_id = employee.get('id', None)
                if employee.get("designation") == "Delivery Man":
                    deliveryman_id = employee.get('id', None)
                instance['duty_start'] = datetime.strptime(employee.get('duty_start', None).split('.')[0], settings.DATE_TIME_FORMATS[2])
                instance['duty_end'] = datetime.strptime(employee.get('duty_end', None).split('.')[0], settings.DATE_TIME_FORMATS[2])
                instance['ot_start'] = employee.get('ot_start', None)
                instance['ot_start'] = None if instance['ot_start'] is None else datetime.strptime(instance['ot_start'].split('.')[0], settings.DATE_TIME_FORMATS[2])
                instance['total_ot'] = employee.get('total_ot', None)
                instance['total_ot'] = None if instance['total_ot'] is None else datetime.strptime(instance['total_ot'].split('.')[0] , settings.DATE_TIME_FORMATS[3]).time()
                instance['ot_payment'] = employee.get('ot_payment', 0)
                instance['tiffin'] = employee.get('tiffin', 0)
                instance['ot_allowance'] = employee.get('ot_allowance', 0)
                instance['hotel'] = employee.get('hotel', 0)
                instance['allowance'] = employee.get('allowance', 0)
                if employee.get("designation") == "Driver":
                    instance, _ = EmployeeReport.objects.update_or_create(duty_log_book_id=duty_log_book_id, driver_id=driver_id, defaults=instance)
                if employee.get("designation") == "Delivery Man":
                    instance, _ = EmployeeReport.objects.update_or_create(duty_log_book_id=duty_log_book_id, deliveryman_id=deliveryman_id, defaults=instance)
                dict_instance = to_dict(instance)
                dict_instance['designation'] = employee.get("designation")
                dict_instance['name'] = instance.driver.name if dict_instance['designation'] == "Driver" else instance.deliveryman.name
                result['employees'].append(dict_instance)
            return JsonResponse(result)
    elif request.method == 'GET':
        vehicle_id = request.GET.get('vehicle_id', None)
        logdate = datetime.strptime(request.GET.get('logdate', None), settings.DATE_INPUT_FORMATS[1])
        try: 
            dutylog = DutyLogBook.objects.get(vehicle_id=vehicle_id, logdate=logdate)
        except DutyLogBook.DoesNotExist:
            return JsonResponse({'detail' : "No Generated Logbook found"}, status=400)
        result['dutylog'] = to_dict(dutylog) # .values().first()
        employees = EmployeeReport.objects.filter(duty_log_book_id=result['dutylog']['id'])
        for employee in employees:
            dict_instance = to_dict(employee)
            dict_instance['designation'] = "Driver" if dict_instance.get("driver", None) is not None else "Delivery Man"
            dict_instance['name'] = employee.driver.name if employee.driver is not None else employee.deliveryman.name 
            result['employees'].append(dict_instance)
        return JsonResponse(result)
    elif request.method == 'PUT':
        data = request.data
        vehicle_id = data.get('vehicle_id', None)
        logdate = datetime.strptime(data.get('logdate', None), settings.DATE_INPUT_FORMATS[1])
        return Response({'exists':DutyLogBook.objects.filter(vehicle_id=vehicle_id, logdate=logdate).exists()})        


@api_view(['GET'])
@permission_classes([IsSuperUser])
def get_duty_info(request):
    result = {}
    vehicle_id = request.GET.get('vehicle_id', None)
    tripdate = datetime.strptime(request.GET.get('trip_date', None), settings.DATE_INPUT_FORMATS[1])
    # if vehicle_id==str(2) and tripdate == tripdate.replace(year=2021, month=12, day=19, hour=0, minute=0, second=0, microsecond=0):
    #     demo = TripInfo()
    #     demo.trip_date = tripdate
    #     demo.trip_start_time = tripdate.replace(year=2021, month=12, day=19, hour=8, minute=0, second=0, microsecond=0)
    #     demo.trip_end_time = tripdate.replace(year=2021, month=12, day=19, hour=17, minute=0, second=0, microsecond=0)
    #     demo.driver = Driver.objects.get(id=1)
    #     demo.vehicle = Vehicle.objects.get(id=2)
    #     demo.warehouse = WareHouse.objects.get(id=2)
    #     demo.trip_status = 3
    #     demo.current_sequence = 2
    #     demo.return_route_distance = 29
    #     result = {}
    #     result['gatepass_data'] = get_gatepass_data(tripdate, 'DH-M-11-5930')
    #     result['vehicle'] = {'id': 2, 'name': 'DH-M-11-5930'}
    #     result['drivers'] = [employee_data_fetch(demo, Driver.objects.get(id=1), True)]
    #     result['deliverymans'] = [employee_data_fetch(demo, DeliveryMan.objects.get(id=1), True)]
    #     result['destinations'] = [
    #         {
    #             'from': 'Brothers Furniture Ltd. ( Factory Unit 1)',
    #             'to' : 'Gulshan, Dhaka',
    #             'invoice_no' : 'Test 01',
    #             'start_time': str(demo.trip_start_time),
    #             'end_time': str(tripdate.replace(year=2021, month=12, day=19, hour=12, minute=0, second=0, microsecond=0)),
    #             'unloading_time' : str(timedelta(hours=1)),
    #             'distance': 27,
    #             'running_time' : str(timedelta(hours=4))
    #         },
    #         {
    #             'from': 'Gulshan, Dhaka',
    #             'to' : 'Mirpur, Dhaka',
    #             'invoice_no' : 'Test 02',
    #             'start_time': str(tripdate.replace(year=2021, month=12, day=19, hour=13, minute=0, second=0, microsecond=0)),
    #             'end_time': str(tripdate.replace(year=2021, month=12, day=19, hour=15, minute=32, second=0, microsecond=0)),
    #             'unloading_time' : str(timedelta(minutes=28)),
    #             'distance': 8.6,
    #             'running_time' : str(timedelta(hours=2, minutes=32))
    #         },
    #         {
    #             'from': 'Mirpur, Dhaka',
    #             'to' : 'Brothers Furniture Ltd. ( Factory Unit 1)',
    #             'invoice_no' : None,
    #             'start_time': str(tripdate.replace(year=2021, month=12, day=19, hour=16, minute=0, second=0, microsecond=0)),
    #             'end_time': str(demo.trip_end_time),
    #             'unloading_time' : None,
    #             'distance': demo.return_route_distance,
    #             'running_time' : str(timedelta(hours=1)),
    #         }
    #     ]
    #     return Response(result)

    dutylog = DutyLogBook.objects.filter(vehicle_id=vehicle_id, logdate=tripdate)
    if dutylog.exists():
        dutylog = dutylog[0]
        vehicle = dutylog.vehicle
        result['gatepass_data'] = get_gatepass_data(tripdate, vehicle.title)
        result['vehicle'] = {'id': vehicle.id, 'name': vehicle.title}
        result['vehicle_info'] = {
            'fuel_reserve': dutylog.fuel_reserve,
            'fuel_purchase': dutylog.fuel_purchase,
            'start_fuel': dutylog.start_fuel,
            'fuel_consumption': dutylog.fuel_consumption,
            'end_fuel': dutylog.end_fuel,
            'fuel_cost': dutylog.fuel_cost,
            'toll_fuel_cost': dutylog.toll_fuel_cost,
            'others_fuel_cost': dutylog.others_fuel_cost,
            'start_vehicle_cost': dutylog.start_vehicle_cost,
            'end_vehicle_cost': dutylog.end_vehicle_cost,
            'start_reading': dutylog.destinations[0]["start_reading"],
        }
        employees = EmployeeReport.objects.filter(duty_log_book_id=dutylog.id)
        result['drivers'] = []
        result['deliverymans'] = []
        for employee in employees:
            if employee.driver is not None:
                result['drivers'].append(
                    {
                        'id' : employee.driver.id,
                        'name': employee.driver.name,
                        'designation': employee.driver.designation,
                        'duty_start': employee.duty_start, 
                        'duty_end': employee.duty_end, 
                        'ot_start': employee.ot_start,
                        'total_ot': employee.total_ot,
                        'ot_payment': employee.ot_payment,
                        'tiffin': employee.tiffin,
                        'ot_allowance': employee.ot_allowance,
                        'hotel': employee.hotel,
                        'allowance': employee.allowance,
                    }
                )
            else:
                result['deliverymans'].append(
                    {
                        'id' : employee.deliveryman.id,
                        'name': employee.deliveryman.name,
                        'designation': employee.deliveryman.designation,
                        'duty_start': employee.duty_start, 
                        'duty_end': employee.duty_end, 
                        'ot_start': employee.ot_start,
                        'total_ot': employee.total_ot,
                        'ot_payment': employee.ot_payment,
                        'tiffin': employee.tiffin,
                        'ot_allowance': employee.ot_allowance,
                        'hotel': employee.hotel,
                        'allowance': employee.allowance,
                    }
                )
        result['destinations'] = dutylog.destinations
        return Response(result)
    area = bool(request.GET.get('area', 0))
    trips = TripInfo.objects.filter(vehicle_id=vehicle_id, trip_date=tripdate, \
            trip_status = TRIP_STATUS['Complete']).order_by('-trip_start_time')
    if not trips.exists():
        raise ValidationError(detail='No finished trip yet!')

    vehicle = trips[0].vehicle
    result['gatepass_data'] = get_gatepass_data(tripdate, vehicle.title)
    result['vehicle'] = {'id': vehicle.id, 'name': vehicle.title}
    result['vehicle_info'] = {
        'fuel_reserve': 0.0,
        'fuel_purchase': 0.0,
        'start_fuel': 0.0,
        'fuel_consumption': 0.0,
        'end_fuel': 0.0,
        'fuel_cost': 0.0,
        'toll_fuel_cost': 0.0,
        'others_fuel_cost': 0.0,
        'start_vehicle_cost': 0.0,
        'end_vehicle_cost': 0.0,
        'start_reading': 0.0,
    }
    result['drivers'] = []
    result['deliverymans'] = []
    result['destinations'] = []
    for trip in trips:
        driver = trip.driver
        if not result['drivers']:
            result['drivers'].append(employee_data_fetch(trip, driver, area))
        else:
            emp = next(filter(lambda x: (x['designation']==driver.designation and  x['id']==driver.id), result['drivers']))
            if emp:
                result['drivers'].remove(emp)
                emp = existing_employee_data_fetch(trip, emp, driver.salary, area)
                result['drivers'].insert(0, emp)
            else:
                result['drivers'].append(employee_data_fetch(trip, driver, area))
        deliverymans = TripDeliveryMan.objects.filter(trip_info=trip)
        if not result['deliverymans']:
            for deliveryman in deliverymans:
                deliveryman = deliveryman.deliveryman
                result['deliverymans'].append(employee_data_fetch(trip, deliveryman, area))
        else:
            for deliveryman in deliverymans:
                deliveryman = deliveryman.deliveryman
                demp = next(filter(lambda x: (x['designation']==deliveryman.designation and  x['id']==deliveryman.id), result['deliverymans']))
                if demp:
                    result['deliverymans'].remove(demp)
                    demp = existing_employee_data_fetch(trip, demp, deliveryman.salary, area)
                    result['deliverymans'].append(demp)
                else:
                    result['deliverymans'].append(employee_data_fetch(trip, deliveryman, area))
        destinations = Destinations.objects.filter(trip_info=trip).order_by('sequence')
        destination_count = destinations.count()
        for d in range(destination_count+1):
            if d!=destination_count:
                destination=destinations[d]
            else:
                destination=None
            if destination is not None:
                previous_destination = destinations.get(sequence=destination.sequence-1) if destination.sequence > 1 else None
                data = {
                        'from': trip.warehouse.name if destination.sequence==1 \
                            else previous_destination.invoice.delivery_address,
                        'to': destination.invoice.delivery_address,
                        'invoice_no': destination.invoice.invoice_id,
                        'start_time': trip.trip_start_time if destination.sequence==1 \
                            else previous_destination.exit_time,
                        'end_time': destination.reach_time,
                        'unloading_time' : str(destination.exit_time-destination.reach_time).split('.')[0] if (destination.reach_time \
                                            and destination.exit_time) is not None else "0:00:00",
                        'distance' : round(destination.route_distance,2)
                    }
                data['running_time'] = str(data['end_time']-data['start_time']).split('.')[0] if (data['start_time'] \
                                            and data['end_time']) is not None and data['start_time']<data['end_time'] else "0:00:00",
                data['start_time'] = str(data['start_time'])
                data['end_time'] = str(data['end_time'])
                
            else:
                previous_destination = destinations.last()
                data = {
                        'from': previous_destination.invoice.delivery_address,
                        'to': trip.warehouse.name,
                        'invoice_no': None,
                        'start_time': previous_destination.exit_time,
                        'end_time': trip.trip_end_time,
                        'unloading_time' : None,
                        'distance' : round(float(trip.return_route_distance),2) if trip.return_route_distance is not None else None
                    }
                data['running_time'] = str(data['end_time']-data['start_time']).split('.')[0] if (data['start_time'] \
                                            and data['end_time']) is not None and data['start_time']<data['end_time'] else "0:00:00",
                data['start_time'] = str(data['start_time'])
                data['end_time'] = str(data['end_time'])
            result['destinations'].append(data)
    return Response(result)

    
