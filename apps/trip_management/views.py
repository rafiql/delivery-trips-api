from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.base.api import CustomViewSet
from apps.user.permission import IsSuperUser
from apps.user.config import ROLE_DICT
from .models import Invoice, SalesPerson, SalesPoint, Driver, Vehicle, WareHouse
from .serializers import *
from .helpers import *


class InvoiceViewSet(CustomViewSet):
    lookup_value_regex = '.+'
    permission_classes = (IsAuthenticated, )
    ObjModel = Invoice
    ObjSerializer = InvoiceSerializer
    ObjSearchFields = ['invoice_id', 'estimated_delivery_date']
    ObjGetSearchFields = ['id', 'invoice_id', 'delivery_status']

    def obj_filter(self, request):
        if request.user.role == ROLE_DICT['SalesManager']:
            return self.ObjModel.objects.filter(sales_point = request.user.salespoint)
        return self.ObjModel.objects.all()

    def get_obj_details(self, obj):
        return get_invoice_data(obj)
    
    def retrieve(self, request, pk, format=None):
        obj_qs = self.obj_filter(request)
        obj = obj_qs.filter(invoice_id=pk)
        if len(obj) < 1:
            obj = obj_qs.filter(id=pk)
        #obj_qs = self.extra_filter_single(obj_qs)
        if len(obj) < 1:
            resp = {'detail': "Object not found."}
            return Response(resp, status=400)
        obj_instance = obj[0]
        self.check_object_permissions(request, obj_instance)
        obj_details = self.get_obj_details(obj_instance)
        return Response(obj_details, status=200)

class SalesPointViewSet(CustomViewSet):
    permission_classes = (IsAuthenticated, )
    ObjModel = SalesPoint
    ObjSerializer = SalesPointSerializer
    ObjSerializer2 = SalesPointSerializerPartial
    ObjSearchFields = ['name', 'address', 'showroom_code']
    ObjGetSearchFields = ['id', 'name', 'address', 'showroom_code']

    def obj_filter(self, request):
        if request.user.role == ROLE_DICT['SalesManager']:
            return self.ObjModel.objects.filter(id = request.user.salespoint.id)
        return self.ObjModel.objects.all()

    def get_obj_details(self, obj):
        return get_salespoint_data(obj)

    def partial_update(self, request, pk, format=None):

        obj_qs = self.ObjModel.objects.filter(id=pk)
        if len(obj_qs) > 0:
            obj_instance = obj_qs[0]
            serializer = self.ObjSerializer2(
                data=request.data,
                context={'request': request, 'view': self}
            )
            self.check_object_permissions(request, obj_instance)
            if serializer.is_valid():
                obj_instance = serializer.update_obj(
                    obj_instance, serializer.validated_data
                )
                data = self.get_obj_details(obj_instance)
                return Response(data, status=200)
            return Response(serializer.errors, status=400)
        return Response({'details': 'Object not found!'}, status=400)

class DriverViewSet(CustomViewSet):
    permission_classes = (IsAuthenticated, )
    ObjModel = Driver
    ObjSerializer = DriverSerializer
    ObjSearchFields = ['name']
    ObjGetSearchFields = ['id', 'name']
    def get_obj_details(self, obj):
        return get_driver_data(obj)


class DeliveryManViewSet(CustomViewSet):
    permission_classes = (IsAuthenticated, )
    ObjModel = DeliveryMan
    ObjSerializer = DeliveryManSerializer
    ObjSearchFields = ['name']
    ObjGetSearchFields = ['id', 'name']
    def get_obj_details(self, obj):
        return get_deliveryman_data(obj)


class VehiclesViewSet(CustomViewSet):
    permission_classes = (IsAuthenticated, )
    ObjModel = Vehicle
    ObjSerializer = VehicleSerializer
    ObjSearchFields = ['title']
    ObjGetSearchFields = ['id', 'title']

    def get_obj_details(self, obj):
        return get_vehicle_data(obj)


class WareHouseViewSet(CustomViewSet):
    permission_classes = (IsAuthenticated, )
    ObjModel = WareHouse
    ObjSerializer = WareHouseSerializer
    ObjSearchFields = ['name']
    ObjGetSearchFields = ['id', 'name', 'address']

    def get_obj_details(self, obj):
        return get_warehouse_data(obj)


class SalesPersonViewSet(CustomViewSet):
    permission_classes = (IsAuthenticated, )
    ObjModel = SalesPerson
    ObjSerializer = SalesPersonSerializer

    def get_obj_details(self, obj):
        return get_salesperson_data(obj)
