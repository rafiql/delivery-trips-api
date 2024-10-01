from decimal import Decimal
import logging
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.base.map_helpers import auto_complete_google, auto_complete_dingi, get_geocode_google_map
from apps.base.models import BaseEntity
from apps.trip_management.config import DELIVERY_STATUS, DELIVERY_CHOICES, TRIP_STATUS, TRIP_CHOICES
from apps.trip_management.geofence import get_list_distance

logger = logging.getLogger(__name__)

# Admin, Sales Manager, 
class SalesPerson(BaseEntity):
    name = models.CharField(max_length=256)


class SalesPoint(BaseEntity):
    name = models.CharField(max_length=256, null=True, blank=True)
    address = models.CharField(max_length=256, null=True, blank=True)
    showroom_code = models.CharField(max_length=256, unique=True)
    lon = models.FloatField(null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)


class WareHouse(BaseEntity):
    name = models.CharField(max_length=256)
    address = models.CharField(max_length=256)
    lon = models.FloatField()
    lat = models.FloatField()


class Driver(BaseEntity):
    name = models.CharField(max_length=200, null=True,  blank=True)
    address = models.CharField(max_length=200, null=True,  blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    license_issue_date = models.DateField(null=True, blank=True)
    license_expiry_date = models.DateField(null=True,  blank=True)
    license_number = models.CharField(max_length=30, null=True, unique=True)
    phone_no = models.CharField(max_length=30)
    note = models.CharField(max_length=255, null=True, blank=True)
    salary = models.FloatField(default=0.0)
    duty_hours = models.PositiveSmallIntegerField(default=10)
    designation = models.CharField(max_length=255, default="Driver")


class DeliveryMan(BaseEntity):
    name = models.CharField(max_length=200, null=True,  blank=True)
    salary = models.FloatField(default=0.0)
    designation = models.CharField(max_length=255, default="Delivery Man")
    driver = models.ForeignKey(Driver, on_delete=models.DO_NOTHING, blank=True, null=True)
    duty_hours = models.PositiveSmallIntegerField(default=10)


class Vehicle(BaseEntity):
    imei = models.CharField(max_length=255, unique=True)
    license_plate = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    title = models.CharField(max_length=100)
    driver = models.ForeignKey(Driver, on_delete=models.DO_NOTHING, blank=True, null=True)

    purchase_date = models.DateField(null=True, blank=True)
    build_year = models.CharField(max_length=20, null=True, blank=True)
    vehicle_icon = models.CharField(max_length=200, null=True, blank=True)
    brand = models.CharField(max_length=100, null=True, blank=True)
    model_number = models.CharField(max_length=100, null=True, blank=True)
    chassis_number = models.CharField(max_length=100, null=True, blank=True)
    engine_number = models.CharField(max_length=100, null=True, blank=True)
    registration_number = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=100, null=True, blank=True)
    body_type = models.CharField(max_length=100, null=True, blank=True)
    fuel_capacity = models.DecimalField(default=40, max_digits=9, decimal_places=4)
    kpl = models.DecimalField(default=8, max_digits=9, decimal_places=4, blank=True,
                              validators=[MinValueValidator(Decimal('0.01'))])

    fuel_reading_status = models.BooleanField(default=False)
    formula = models.TextField(null=True, blank=True)
    refuel_percentage_threshold = models.DecimalField(null=True, max_digits=9, decimal_places=4, blank=True)
    refuel_ltr_threshold = models.DecimalField(null=True, max_digits=9, decimal_places=4, blank=True)
    leakage_percentage_threshold = models.DecimalField(null=True, max_digits=9, decimal_places=4, blank=True)
    leakage_ltr_threshold = models.DecimalField(null=True, max_digits=9, decimal_places=4, blank=True)
    fuel_speed_threshold = models.DecimalField(null=True, max_digits=9, decimal_places=4, blank=True)
    fuel_data_delay = models.IntegerField(null=True, blank=True)

    height = models.DecimalField(null=True, blank=True, default=0.0, decimal_places=6, max_digits=20)
    weight = models.DecimalField(null=True, blank=True, default=0.0, decimal_places=6, max_digits=20)
    width = models.DecimalField(null=True, blank=True, default=0.0, decimal_places=6, max_digits=20)
    address = models.CharField(max_length=255, null=True, blank=True)


class Invoice(BaseEntity):
    invoice_id = models.CharField(max_length=255, unique=True)
    delivery_status = models.PositiveSmallIntegerField(default=DELIVERY_STATUS['Pending'], choices= DELIVERY_CHOICES)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    selling_date = models.DateField(null=True, blank=True)
    sales_point = models.ForeignKey(SalesPoint, on_delete=models.CASCADE)
    sales_person = models.ForeignKey(SalesPerson,on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=255)
    delivery_address = models.CharField(max_length=255)
    customer_phone_no = models.CharField(max_length=15)
    remarks = models.CharField(max_length=255, null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    radius = models.PositiveSmallIntegerField(default=100)

    def get_delivery_address(self):
        return self.delivery_address

    def save(self, *args, **kwargs):
        if self.lon is None or self.lat is None:
            try:
                self.lat, self.lon = get_geocode_google_map(self.delivery_address)
            except:
                self.lat, self.lon = auto_complete_dingi(self.delivery_address)['result'][0]['location']
                self.radius = 500
        super(Invoice, self).save(*args, **kwargs)

class Destinations:
    pass

class TripInfo(BaseEntity):
    trip_date = models.DateField()
    trip_start_time = models.DateTimeField(null=True, blank=True)
    trip_end_time = models.DateTimeField(null=True, blank=True)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(WareHouse, on_delete=models.CASCADE)
    trip_status = models.PositiveSmallIntegerField(default=TRIP_STATUS['Scheduled'], choices= TRIP_CHOICES)
    current_sequence = models.PositiveSmallIntegerField(default=0)
    vehicle_location = JSONField(null=True, blank=True)
    return_route_history = JSONField(default=list, null=True, blank=True)
    return_route_distance = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.trip_status == TRIP_STATUS['Complete']:
            try:
                last_destination = Destinations.objects.filter(trip_info_id=self.id).order_by('-sequence')[0]
                invoice = last_destination.invoice
                warehouse = self.warehouse
                warehouse_location = {'lon':warehouse.lon, 'lat':warehouse.lat}
                invoice_location = {'lon': invoice.lon, 'lat': invoice.lat}
                distance_route = self.return_route_history
                distance_route.insert(0, invoice_location)
                distance_route.append(warehouse_location)
                self.return_route_distance = get_list_distance(distance_route)
            except Exception as e:
                logger.error('Something went wrong! '+str(e))
        super(TripInfo, self).save(*args, **kwargs)
    

class TripDeliveryMan(models.Model):
    trip_info = models.ForeignKey(TripInfo, on_delete=models.CASCADE)
    deliveryman = models.ForeignKey(DeliveryMan, on_delete=models.DO_NOTHING)


class Destinations(BaseEntity):
    trip_info = models.ForeignKey(TripInfo, on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.DO_NOTHING)
    sequence = models.PositiveSmallIntegerField()
    sms_status = models.PositiveSmallIntegerField(null=True, blank=True)
    reach_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    route_history = JSONField(default=list, null=True, blank=True)
    route_distance = models.FloatField(null=True, blank=True)

@receiver(post_save, sender=Invoice)
def route_distance_updater(sender, instance, **kwargs):
    if instance.delivery_status == DELIVERY_STATUS['Delivered']:
        try:
            obj = Destinations.objects.filter(invoice_id=instance.id, route_distance__isnull=True).order_by('-created_at').first()
            if obj.sequence == 1:
                start_location = obj.trip_info.warehouse
            else:
                previous_destination = Destinations.objects.filter(trip_info=obj.trip_info, sequence=obj.sequence-1)[0]
                start_location = previous_destination.invoice
            start_location = {'lon':start_location.lon, 'lat':start_location.lat}
            invoice_location = {'lon': instance.lon, 'lat': instance.lat}
            distance_route = obj.route_history
            distance_route.insert(0, start_location)
            distance_route.append(invoice_location)
            obj.route_distance = get_list_distance(distance_route)
            obj.save()
        except Exception:
            logger.error('Something went wrong! '+str(Exception))
