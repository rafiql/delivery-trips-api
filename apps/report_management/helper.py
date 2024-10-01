import requests
from datetime import timedelta
from django.conf import settings
from rest_framework.exceptions import ValidationError

GATE_PASS_URL='https://bpos.ictlayer.app/api/memo_details/'

def get_gatepass_data(trip_date, vehicle):
    trip_date_str = trip_date.strftime(settings.DATE_INPUT_FORMATS[1])
    response_result = requests.get(GATE_PASS_URL+trip_date_str+'/'+trip_date_str)
    if 200 <= response_result.status_code < 300:
        response_result = response_result.json()[0]
        data = list(filter(lambda x: (x['car_number']==vehicle), response_result))
        result  = {
            'gatepass' :[],
            'total_delivery_value_dp' :0,
            'total_delivery_value_sp' :0,
        }
        for d in data:
            result['gatepass'].append(d['gate_pass_no']+':'+d['showroom_name'])
            result['total_delivery_value_dp'] += float(d['memo_total_dp_value'])
            result['total_delivery_value_sp'] += float(d['memo_total_sp_value'])
        if not result['gatepass']:
            raise ValidationError(detail='No gatepass found')
        return result
    else:
        raise ValidationError(detail='get memo details api failed!')


def employee_data_fetch(trip, employee, area):
    dutyseconds = employee.duty_hours*3600
    ot_start_time = trip.trip_start_time+timedelta(hours=employee.duty_hours)
    workseconds = (trip.trip_end_time-trip.trip_start_time).seconds
    not_ot = workseconds <= dutyseconds
    data = {
            'id': employee.id,
            'name': employee.name,
            'designation': employee.designation,
            'duty_start': str(trip.trip_start_time),
            'duty_end': str(trip.trip_end_time),
            'dutyseconds' : dutyseconds,
            'workseconds' : workseconds,
            'ot_start': None if not_ot else str(ot_start_time).split('.')[0],
            'total_ot' : None if not_ot else str(timedelta(seconds=(workseconds-dutyseconds))).split('.')[0],
            'ot_payment' : None if not_ot else round((employee.salary/2592000)*(workseconds-dutyseconds),2)\
                         if area else 250 if employee.designation=="Driver" else 150,
            'tiffin' : 70 if area else 250 if employee.designation=="Driver" else 225,
            'ot_allowance' : None if not_ot else 20 if area else None,
            'hotel' : None if area else 200 if employee.designation=="Driver" else 150,
            'allowance' : 0,
            'one_day_salary' : round(employee.salary/30, 2)
        }
    return data

def existing_employee_data_fetch(trip, emp, salary, area):
    not_ot = emp['workseconds'] <= emp['dutyseconds']
    emp['duty_end'] = str(trip.trip_end_time)
    emp['workseconds'] += (trip.trip_end_time-trip.trip_start_time).seconds
    emp['total_ot'] = None if not_ot else str(timedelta(seconds=(emp['workseconds']-emp['dutyseconds']))).split('.')[0]
    if emp['ot_start'] is None and not not_ot:
        ot_start_time = trip.trip_start_time+timedelta(hours=emp['dutyseconds']/3600)
        emp['ot_start'] = str(ot_start_time).split('.')[0]
    if area:
        emp['ot_payment'] = None if not_ot else round((salary/2592000)*(emp['workseconds']-emp['dutyseconds']), 2)
        if trip.trip_end_time > trip.trip_end_time.replace(hour=20, minute=0, second=0, microsecond=0):
            emp['tiffin'] += 70
    else:
        emp['ot_payment'] += 250 if emp['designation'].designation=="Driver" else 150
        emp['hotel'] += 200 if emp['designation'].designation=="Driver" else 150
    return emp