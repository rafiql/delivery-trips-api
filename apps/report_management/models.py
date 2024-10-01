from datetime import datetime
from decimal import Decimal
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.contrib.postgres.fields import JSONField
from apps.base.models import BaseEntity
from apps.trip_management.models import TripInfo, Vehicle, Driver, DeliveryMan


class DutyLogBook(BaseEntity):
    logdate = models.DateTimeField()

    gatepass = JSONField(default=list, null=True, blank=True)
    total_delivery_value_dp = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    total_delivery_value_sp = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    total_delivery_cost = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    other_delivery_value = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    dp_percent =  models.FloatField(default=0.0)
    sp_percent =  models.FloatField(default=0.0)

    vehicle = models.ForeignKey(Vehicle, on_delete=models.DO_NOTHING)
    fuel_reserve = models.FloatField(default=0.0)
    fuel_purchase = models.FloatField(default=0.0)
    start_fuel = models.FloatField(default=0.0)
    fuel_consumption = models.FloatField(default=0.0)
    end_fuel = models.FloatField(default=0.0)
    fuel_cost  = models.FloatField(default=0.0)
    toll_fuel_cost  = models.FloatField(default=0.0)
    others_fuel_cost  = models.FloatField(default=0.0)
    total_vehicle_cost = models.FloatField(default=0.0)
    start_vehicle_cost = models.FloatField(default=0.0)
    end_vehicle_cost = models.FloatField(default=0.0)
    total_ot_payment = models.FloatField(default=0.0)
    total_tiffin = models.FloatField(default=0.0)
    total_ot_allowance = models.FloatField(default=0.0)
    total_hotel = models.FloatField(default=0.0)
    total_allowance = models.FloatField(default=0.0)
    destinations = JSONField(default=list, null=True, blank=True)
    total_distance = models.FloatField(default=0.0)
    cost_per_kilo = models.FloatField(default=0.0)
    total_one_day_salary = models.FloatField(default=0.0)


class EmployeeReport(models.Model):
    duty_log_book = models.ForeignKey(DutyLogBook, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.DO_NOTHING, blank=True, null=True)
    deliveryman = models.ForeignKey(DeliveryMan, on_delete=models.DO_NOTHING, blank=True, null=True)
    duty_start = models.DateTimeField(blank=True, null=True)
    duty_end = models.DateTimeField(blank=True, null=True)
    ot_start = models.DateTimeField(blank=True, null=True)
    total_ot = models.TimeField(blank=True, null=True)
    ot_payment = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    tiffin = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    ot_allowance = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    hotel = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    allowance = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    


