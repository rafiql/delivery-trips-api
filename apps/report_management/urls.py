from django.conf.urls import url
from apps.report_management import api

urlpatterns = [
    url(r'^logbook/get_duty_info/$', api.get_duty_info, name='get_duty_info'),
    url(r'^logbook/dutyloggerentry/$', api.dutyloggerentry, name='dutylogger'),
]