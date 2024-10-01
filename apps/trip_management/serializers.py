from django.db import models
from django.db.models import fields
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.exceptions import NotAcceptable, ValidationError, PermissionDenied
from apps.base.serializers import CustomSerializer, CustomAuthSerializer
from .models import *
from apps.user.config import ROLE_DICT




class InvoiceSerializer(ModelSerializer):

    class Meta:
        model = Invoice
        fields = '__all__'
        extra_kwargs = {
            'invoice_id': {'validators': []},
        }

    def create_obj(self, validated_data):
        # print(self.context)

        invoice = self.create(validated_data)
        return invoice

    def update_obj(self, invoice, validated_data):
        # print(self.context)
        user = self.context['request'].user
        valid_role = [ ROLE_DICT['Manager'], ROLE_DICT['Admin']]
        if user.role not in valid_role:
            raise PermissionDenied(detail='Permission Denied!')

        invoice = self.update(invoice, validated_data)
        return invoice


class SalesPointSerializer(CustomAuthSerializer):

    class Meta:
        model = SalesPoint
        fields = '__all__'


class SalesPointSerializerPartial(CustomAuthSerializer):
    class Meta:
        model = SalesPoint
        exclude = ['showroom_code']

    def update_obj(self, salespoint, validated_data):
        # print(self.context)
        user = self.context['request'].user
        valid_role = [ ROLE_DICT['Manager'], ROLE_DICT['Admin']]
        if user.role not in valid_role:
            raise PermissionDenied(detail='Permission Denied!')
        if validated_data.get("showroom_code") == salespoint.showroom_code:
            validated_data.pop("showroom_code")
        salespoint = self.update(salespoint, validated_data)
        return salespoint
        


class DriverSerializer(CustomAuthSerializer):

    class Meta:
        model = Driver
        fields = '__all__'
        extra_kwargs = {
            'license_number': {'validators': []},
        }


class DeliveryManSerializer(CustomAuthSerializer):

    class Meta:
        model = DeliveryMan
        fields = '__all__'


class VehicleSerializer(CustomAuthSerializer):

    class Meta:
        model = Vehicle
        fields = '__all__'
        extra_kwargs = {
            'imei': {'validators': []},
        }


class WareHouseSerializer(CustomAuthSerializer):

    class Meta:
        model = WareHouse
        fields = '__all__'


class SalesPersonSerializer(CustomAuthSerializer):

    class Meta:
        model = SalesPerson
        fields = '__all__'


class TripInfoSerializer(CustomAuthSerializer):
    
    class Meta:
        model = TripInfo
        fields = '__all__'


class DestinationsSerializer(CustomAuthSerializer):

    class Meta:
        model = Destinations
        fields = '__all_'