from django.conf.urls import url
from rest_framework import routers
from apps.trip_management.views import InvoiceViewSet, SalesPersonViewSet, SalesPointViewSet, DriverViewSet,\
     VehiclesViewSet, WareHouseViewSet, DeliveryManViewSet
from . import api

router = routers.DefaultRouter()
router.register('invoice', InvoiceViewSet, basename='invoice_object')
# router.register('invoice_search', InvoiceGetViewSet, basename='invoice_search')
router.register('salespoint', SalesPointViewSet, basename='salespoint_object')
router.register('driver', DriverViewSet, basename='driver_object')
router.register('deliveryman', DeliveryManViewSet, basename='deliveryman_object')
router.register('vehicle', VehiclesViewSet, basename='vehicles_object')
router.register('warehouse', WareHouseViewSet, basename='warehouse_object')
router.register('salesperson', SalesPersonViewSet, basename='salesperson_object')


urlpatterns = [
    url(r'^api/trip_scheduler_sorter/$', api.trip_scheduler_sorter, name='trip_scheduler_sorter'),
    url(r'^api/invoice_by_date/$', api.invoice_by_date, name='invoice_by_date'),
    url(r'^api/trip_scheduler/$', api.trip_scheduler, name='trip_scheduler'),
    url(r'^api/tracker/$', api.tracker, name='tracker'),
    url(r'^api/get_scheduled_trip/$', api.get_scheduled_trip, name='get_scheduled_trip'),
    url(r'^api/delete_trip/$', api.trip_deletion, name='trip_deletion'),
    url(r'^api/modify_destination/$', api.destination_mod, name='destination_mod'),
    url(r'^invoice_search/$', api.invoice_search, name='invoice_search'),
    url(r'^delivery_count/$', api.delivery_count, name='delivery_count'),
    url(r'^vehicle_search/$', api.vehicle_search, name='vehicle_search'),
    url(r'^deliveryman_search/$', api.deliveryman_search, name='deliveryman_search'),
    url(r'^address_search/$', api.address_search, name='address_search'),
    url(r'^get_invoices/$', api.call_get_invoice, name='get_invoices'),
    url(r'^reverse_geocode/$', api.geocode_to_address, name='reverse_geocode'),
]

urlpatterns += router.urls