from django.core.management.base import BaseCommand
from django.conf import settings
import requests
from datetime import datetime
from apps.base.config import *
from apps.trip_management.config import *
from apps.trip_management.models import Invoice, SalesPerson, SalesPoint
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            invoices = requests.get(
                GET_INVOICE_API,
                timeout=REQ_TIMEOUT,
                )
            if 200 <= invoices.status_code < 300:
                invoice_data = invoices.json()
                invoice_data = invoice_data[0]

                for invoice in invoice_data:
                    check_invoice = Invoice.objects.filter(invoice_id=invoice['memo_no'])
                    if check_invoice.exists():
                        pass
                    else:
                        instance = Invoice()
                        instance.invoice_id = invoice['memo_no']
                        instance.sales_point , _ = SalesPoint.objects.get_or_create(showroom_code=invoice['showroom_code'])
                        if 'sales_person' in invoice:
                            instance.sales_person, _ = SalesPerson.objects.get_or_create(name=invoice['sales_person'])
                        instance.estimated_delivery_date = datetime.strptime(invoice['delivery_date'], settings.DATE_INPUT_FORMATS[1])
                        try:
                            instance.selling_date = datetime.strptime(invoice['memo_no'].split('-')[1], settings.DATE_INPUT_FORMATS[2])
                        except:
                            try:
                                instance.selling_date = datetime.strptime(invoice['memo_no'].split('-')[2], settings.DATE_INPUT_FORMATS[2])
                            except:
                                instance.selling_date = None
                        instance.customer_name = invoice['customer_name']
                        instance.customer_phone_no = invoice['c_phone']
                        instance.delivery_address = invoice['customer_address']
                        instance.save()
                        print(invoice['memo_no'], " entered successfully")

        except Exception as exc:
            logger.error('Something went wrong! '+str(exc))
