from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from apps.base.config import *
from apps.base.map_helpers import get_vehicle_location
from apps.trip_management.config import *
from apps.trip_management.models import TripInfo, Destinations
from apps.trip_management.geofence import in_fence
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            currentTime = datetime.utcnow()+timedelta(hours=6)
            # startTime = currentTime.replace(hour=8, minute=0, second=0, microsecond=0)
            # if currentTime>startTime:
            trips = TripInfo.objects.filter(trip_date__in=[datetime.now().date(), (datetime.now()-timedelta(days=1)).date()])\
                            .exclude(trip_status=TRIP_STATUS['Complete']).order_by('vehicle','-created_at').distinct('vehicle')
            if trips.exists():
                for trip in trips:
                    vehicle_data = get_vehicle_location(trip.vehicle.imei)
                    vehicle_location = vehicle_data['location']
                    vehicle_location['time'] = str(currentTime)
                    vehicle_location['count'] = 1
                    trip.vehicle_location = vehicle_data
                    destinations = Destinations.objects.filter(trip_info_id=trip.id).order_by('sequence')
                                        # .exclude(invoice__delivery_status=DELIVERY_STATUS['Delivered'])
                    warehouse_location = {
                                            'lon':trip.warehouse.lon, 
                                            'lat':trip.warehouse.lat
                                            }
                    if trip.trip_status == TRIP_STATUS['Scheduled']:
                        if not in_fence(warehouse_location, vehicle_location):
                            first_destination = destinations.first()
                            first_destination.route_history = [vehicle_location]
                            first_destination.save()
                            trip.trip_start_time = currentTime
                            trip.trip_status = TRIP_STATUS['Started']
                            trip.current_sequence = 1
                            trip.save()
                    elif trip.trip_status == TRIP_STATUS['Started']:
                        current_destination = destinations.get(sequence=trip.current_sequence)
                        last_destination = destinations.last()
                        invoice_info = current_destination.invoice
                        if invoice_info.delivery_status==DELIVERY_STATUS['Scheduled']:
                            invoice_info.delivery_status=DELIVERY_STATUS['OnDelivery']
                            invoice_info.save()
                        invoice_location = {
                                            'lon': invoice_info.lon,
                                            'lat': invoice_info.lat
                                            }
                        reached = in_fence(invoice_location, vehicle_location, invoice_info.radius)
                        if not reached and invoice_info.delivery_status==DELIVERY_STATUS['OnDelivery']:
                            if not current_destination.route_history:
                                current_destination.route_history = [vehicle_location]
                            elif (current_destination.route_history[-1]['lon'] == vehicle_location['lon'] \
                                and current_destination.route_history[-1]['lat'] == vehicle_location['lat']):
                                current_destination.route_history[-1]['count'] += 1
                            else:
                                current_destination.route_history.append(vehicle_location)
                            if current_destination.route_history[-1]['count']>=10 \
                                and invoice_info.delivery_status==DELIVERY_STATUS['OnDelivery']:
                                if in_fence(invoice_location, vehicle_location, 1000):
                                    invoice_info.lon = vehicle_location['lon']
                                    invoice_info.lat = vehicle_location['lat']
                                    invoice_info.delivery_status=DELIVERY_STATUS['Unloading']
                                    invoice_info.save()
                                    current_destination.reach_time = \
                                        currentTime-timedelta(minutes=current_destination.route_history[-1]['count'])
                                else:
                                    remaining_destinations =  destinations.filter(sequence__gt=trip.current_sequence)
                                    if remaining_destinations.exists():
                                        fence_check = False
                                        for dest in remaining_destinations:
                                            fence_check = in_fence({'lat':dest.invoice.lat,'lon':dest.invoice.lon}, vehicle_location, 100)
                                            if fence_check:
                                                bk_sequence = dest.sequence
                                                dest.sequence = current_destination.sequence
                                                dest.route_history = current_destination.route_history
                                                dest.invoice.delivery_status=DELIVERY_STATUS['Unloading']
                                                dest.reach_time = \
                                                    currentTime-timedelta(minutes=current_destination.route_history[-1]['count'])
                                                dest.invoice.save()
                                                dest.save()
                                                current_destination.sequence = bk_sequence
                                                current_destination.route_history = []
                                                current_destination.invoice.delivery_status = DELIVERY_STATUS['Scheduled']
                                                current_destination.invoice.save()
                                                current_destination.save()
                                                break
                                        if fence_check:
                                            continue
                            current_destination.save()
                        invoice_location = {
                                            'lon': invoice_info.lon,
                                            'lat': invoice_info.lat
                                            }
                        reached = in_fence(invoice_location, vehicle_location, invoice_info.radius)
                        if reached and invoice_info.delivery_status==DELIVERY_STATUS['OnDelivery']:
                            current_destination.reach_time = currentTime
                            current_destination.save()
                            invoice_info.delivery_status=DELIVERY_STATUS['Unloading']
                            invoice_info.save()
                        elif not reached and invoice_info.delivery_status==DELIVERY_STATUS['Unloading']:
                            invoice_info.delivery_status=DELIVERY_STATUS['Delivered']
                            current_destination.exit_time = currentTime
                            current_destination.save()
                            invoice_info.save()
                            if not current_destination.sequence >= last_destination.sequence:
                                trip.current_sequence += 1
                        if last_destination.invoice.delivery_status==DELIVERY_STATUS['Delivered']:
                            if in_fence(warehouse_location, vehicle_location):
                                trip.trip_end_time = currentTime
                                trip.trip_status = TRIP_STATUS['Complete']
                            else:
                                if not trip.return_route_history:
                                    trip.return_route_history = [vehicle_location]
                                elif (trip.return_route_history[-1]['lon'] == vehicle_location['lon'] \
                                and trip.return_route_history[-1]['lat'] == vehicle_location['lat']):
                                    trip.return_route_history[-1]['count'] += 1
                                else:
                                    trip.return_route_history.append(vehicle_location)
                        elif in_fence(warehouse_location, vehicle_location):
                            remaining_destinations =  destinations.filter(sequence__gt=trip.current_sequence)
                            if remaining_destinations.exists():
                                for destination in remaining_destinations:
                                    destination.reach_time = currentTime.replace(hour=0, minute=0, second=0, microsecond=0)
                                    destination.exit_time = currentTime.replace(hour=0, minute=0, second=0, microsecond=0)
                                    destination.route_distance = 0
                                    destination.invoice.delivery_status=DELIVERY_STATUS['Delivered']
                                    destination.invoice.save()
                                    destination.save()
                            if invoice_info.delivery_status == DELIVERY_STATUS['OnDelivery']:
                                current_destination.reach_time = currentTime.replace(hour=0, minute=0, second=0, microsecond=0)
                            invoice_info.delivery_status=DELIVERY_STATUS['Delivered']
                            invoice_info.save()
                            trip.current_sequence = last_destination.sequence
                            trip.return_route_history = current_destination.route_history + trip.return_route_history
                            trip.trip_end_time = currentTime
                            trip.trip_status = TRIP_STATUS['Complete']
                            current_destination.exit_time = currentTime.replace(hour=0, minute=0, second=0, microsecond=0)
                            current_destination.route_distance = 0
                            current_destination.save()
                        trip.save()
        except Exception as exc:
            logger.error('Something went wrong! '+str(exc))
