from apps.base.utils import dict_to_choice
from datetime import datetime

DELIVERY_STATUS = {'Pending': 1, 'Scheduled': 2, 'OnDelivery': 3, 'Unloading': 4, 'Delivered': 5}
DELIVERY_CHOICES = dict_to_choice(DELIVERY_STATUS)
TRIP_STATUS = {'Scheduled': 1, 'Started': 2, 'Complete': 3}
TRIP_CHOICES = dict_to_choice(TRIP_STATUS)
TRIP_START_HOUR = 8
GET_INVOICE_API = 'https://bflcc.ictlayer.app/api/all_showroom_customer_memos/' \
                  +datetime.now().strftime("%Y-%m-%d")+'/'+datetime.now().strftime("%Y-%m-%d")

host = 'https://tracking.brothersfurniture.com.bd/'

# SMS API
def sms_url_builder(number, msg):
    senderid=1072
    APIKEY='C20001345e325228856331.99153847'
    SMSURL='http://portal.metrotel.com.bd/smsapi?api_key='+str(APIKEY)+'&type=text&senderid='+str(senderid)+\
        '&contacts='+str(number)+'&msg='+str(msg)

    return SMSURL