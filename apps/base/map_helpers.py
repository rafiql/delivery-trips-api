import requests
from apps.trip_management.enums import MapApiProviderEnum
from apps.base.config import *
from conf.settings import GOOGLE_MAP_API_KEY
from .utils import meter_to_km


def get_address_dingi_map_new(latitude, longitude, ):
    if not all([latitude, longitude]):
        return ''

    try:
        geocode_result = requests.get(
            REVERSE_GEOCODE_API_DINGI_NEW,
            timeout=REQ_TIMEOUT,
            params={'lat': latitude, 'lng': longitude, 'language': 'en'},
            headers={'x-api-key': X_API_KEY}
        )
        address = ""
        if 200 <= geocode_result.status_code < 300:
            res_data = geocode_result.json()
            address = f"On {res_data['way']['name']}, {res_data['poi']['distance']}m {res_data['poi']['direction']} from {res_data['poi']['name']}, {res_data['address']}"
        return address
    except Exception as exc:
        return ''


def get_address_dingi_map(latitude, longitude, ):
    if not all([latitude, longitude]):
        return ''

    try:
        geocode_result = requests.get(
            REVERSE_GEOCODE_API_DINGI,
            timeout=REQ_TIMEOUT,
            params={'lat': latitude, 'lng': longitude, 'language': 'en'},
            headers={'x-api-key': X_API_KEY}
        )
    except Exception as exc:
        return ''

    return geocode_result.json()["result"]["address"] if geocode_result.ok else ''


def get_address_google_map(latitude, longitude, ):
    if not all([latitude, longitude]):
        return ''
    try:
        geocode_result = requests.get(
            REVERSE_GEOCODE_API_GOOGLE,
            timeout=REQ_TIMEOUT,
            params={'latlng': f'{latitude},{longitude}', 'key': GOOGLE_MAP_API_KEY}
        )
        if geocode_result.ok:
            return ", ".join(d['address_components'][0]['short_name'] for d in geocode_result.json()["results"])
    except Exception as exc:
        print(exc)
        return ''


def get_geocode_google_map(address):
    if not address:
        return []
    try:
        geocode_result = requests.get(
            REVERSE_GEOCODE_API_GOOGLE,
            timeout=REQ_TIMEOUT,
            params={'address': f'{address}', 'region': "bd", 'key': GOOGLE_MAP_API_KEY}
        )
        if geocode_result.ok:
            result = []
            try:
                reponse = geocode_result.json()["results"][0]
                #if any(filter(lambda x: (x['short_name']=='BD'), reponse['address_components'])):
                result = list(reponse['geometry']['location'].values())
            except:
                result = []
            return result
    except Exception as exc:
        print(exc)
        return []


def get_address(latitude, longitude, provider=1, skip=True):
    if not all([latitude, longitude]):
        return ""

    if skip:
        address = None
    # else:
    #     address = get_geo_code_text(latitude, longitude)
    if not address:
        if provider == MapApiProviderEnum.DingiMap.value:
            address = get_address_dingi_map_new(latitude, longitude)
        else:
            address = get_address_google_map(latitude, longitude)
    return address


def auto_complete_dingi(query):
    search_result = requests.get(AUTOCOMPLETESEARCH_DINGI, params={'token': query},
                                 headers={'x-api-key': X_API_KEY})
    result = []

    if 200 <= search_result.status_code < 300:
        result = search_result.json()
    return result


def auto_complete_google(query):
    search_result = requests.get(
        AUTOCOMPLETESEARCH_GOOGLE,
        params={
            'query': query,
            'region': "bd",
            'key': GOOGLE_MAP_API_KEY}
    )
    result = []

    if 200 <= search_result.status_code < 300:
        data_list = []
        for data in search_result.json()["results"]:
            data_list.append({
                "location": [
                    data["geometry"]["location"]["lat"],
                    data["geometry"]["location"]["lng"]
                ],
                "name": data["name"],
                "address": data["formatted_address"],
            })
        result = {"result": data_list}

    return result


def has_entered_in(location, current_point, prev_point):
    if location.contains(current_point) and not location.contains(prev_point):
        return True
    return False


def has_exit_out(location, current_point, prev_point):
    if location.contains(prev_point) and not location.contains(current_point):
        return True
    return False


def km_to_degree(radius):
    return radius / 40000 * 360


def get_circle(center, radius):
    radius = km_to_degree(meter_to_km(radius))
    circle = center.buffer(radius)
    return circle


def get_vehicle_location(imei):
    result = requests.get(FOLLOWR_LOCATION_TRACKING, params={'imei': imei},
                                 headers={'Authorization': FOLLOWR_X_API_KEY})

    if 200 <= result.status_code < 300:
        result = result.json()
    else:
        result = {}
    return result


def get_fastest_route(source:list, destination:list):
    coordinates = str(source[0])+'a'+str(source[1])+'b'+str(destination[0])+'a'+str(destination[1])
    result = requests.get(ROUTE_DINGI, params={'steps': False, 'criteria': "fastest", 'coordinates':coordinates},
                                 headers={'x-api-key': X_API_KEY})

    if 200 <= result.status_code < 300:
        result = result.json()
    else:
        result = {}
    return result