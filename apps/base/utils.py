import datetime
from dateutil.parser import parse
import pytz
import json, requests
import uuid
from functools import reduce
from random import sample
from shortuuid import ShortUUID
from django.contrib.gis.geos import Polygon, Point
from conf.settings import DATE_TIME_FORMATS
from django.conf import settings

def convert_datetime_to_string(o, date_format="%Y-%m-%d", time_format="%H:%M:%S"):
    if isinstance(o, datetime.datetime):
        return o.isoformat()
    elif isinstance(o, datetime.date):
        return o.strftime(date_format)
    elif isinstance(o, datetime.time):
        return o.strftime(time_format)
    else:
        return o


def get_readable_time(seconds):
    minute, second = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    time = ""

    def get_string(value, unit):
        return f'{int(value)} {unit + "s " if value > 1 else unit}'

    if hour > 0:
        time += get_string(hour, "hour")
    if minute > 0:
        time += get_string(minute, "minute")
    if second > 0:
        time += get_string(second, "second")

    return time


def get_attr_d(obj, name):
    try:
        return reduce(getattr, name.split("."), obj)
    except AttributeError as e:
        return ''


def get_as_dict(choice):
    data = {}
    for val, key in choice:
        data[key] = val
    return data


def dict_to_choice(dict_data):
    temp_choice = tuple((value, key) for key, value in dict_data.items())
    return temp_choice


def get_short_uuid():
    short_u = ShortUUID(alphabet="23456789ABCDEFGHJKLMNPQRSTUVWXYZ")
    return short_u.random(8)


def get_full_uuid():
    return str(uuid.uuid4())


def get_extension(file_name):
    filename_parts = file_name.split(".")
    if len(filename_parts) == 2:
        return filename_parts[1]
    elif len(filename_parts) > 2:
        return filename_parts[-1]
    else:
        return None


def remove_extension(text):
    splitted_data = text.split(".")
    if len(splitted_data) == 2:
        return splitted_data[0]
    elif len(splitted_data) > 2:
        del splitted_data[-1]
        return ''.join(map(str, splitted_data))
    return splitted_data[0]


def json_to_point(field=None):
    if field:
        try:
            field = json.loads(field)
            x = field.get('lon', False)
            y = field.get('lat', False)
            if not (x and y):
                return None
            point_geo = Point(x=x, y=y, srid=4326)
            return point_geo
        except Exception as e:
            print(str(e))
            return None
    return None


def dict_to_point(field=None):
    if field:
        try:
            x = field.get('lon', False)
            y = field.get('lat', False)
            if not (x and y):
                return None
            point_geo = Point(x=x, y=y, srid=4326)
            return point_geo
        except Exception as e:
            print(str(e))
            return None
    return None


def json_to_bound_box(ne=None, sw=None):
    if ne and sw:
        try:
            ne_point = json_to_point(ne)
            sw_point = json_to_point(sw)
            if ne_point and sw_point:
                bbox = (sw_point.x, sw_point.y, ne_point.x, ne_point.y)
                geom = Polygon.from_bbox(bbox)
                return geom
        except Exception as e:
            print(str(e))
            return None
    return None

def get_jwt_token(username, password):
    url = settings.TEST_HOST + "user/api/token/"
    data = {'username': username, 'password': password}
    response = requests.post(url, data)
    response_data = json.loads(response.content)
    return response_data['token']

def make_is_deleted_true(instance):
    if instance and not instance.is_deleted:
        instance.is_deleted = True
        instance.save()

def meter_to_km(distance):
    return round(distance / 1000, 2)