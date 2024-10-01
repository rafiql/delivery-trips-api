from django.contrib.gis.geos import Point
from geopy.distance import distance as geopy_distance
# from haversine import haversine
from shapely.geometry import Point as SP, Polygon
from rest_framework.exceptions import NotAcceptable


#Creates Polygon fence with given location points
def create_fence(points):
    fence = [SP(lng,lat) for lat, lng in points]
    coords = [p.coords[:][0] for p in fence]
    # return SP(coords)
    return Polygon(coords)


def in_fence(source_location, vehicle_location, radius=100):

    source_location = Point(x=float(source_location["lat"]),
                            y=float(source_location["lon"]))
    vehicle_location = Point(x=float(vehicle_location["lat"]), 
                            y=float(vehicle_location["lon"]))
    distance = geopy_distance(source_location,
                            vehicle_location).meters
    if distance <= radius:
        return True
    else:
        return False


def get_distance(source_location, vehicle_location):

    source_location = Point(x=float(source_location["lat"]),
                            y=float(source_location["lon"]))
    vehicle_location = Point(x=float(vehicle_location["lat"]), 
                            y=float(vehicle_location["lon"]))
    distance = geopy_distance(source_location,
                            vehicle_location).meters
    return distance



def get_list_distance(routes:list):
    route_len = len(routes)
    total_distance = 0
    for route in range(route_len-1):
        source_location = routes[route]
        destination_location = routes[route+1]
        source_location = Point(x=float(source_location["lat"]),
                            y=float(source_location["lon"]))
        destination_location = Point(x=float(destination_location["lat"]), 
                            y=float(destination_location["lon"]))
        distance = geopy_distance(source_location,
                            destination_location).meters
        total_distance += distance
    
    return total_distance/1000


def valid_lat_lng(point: tuple):
    """
    This validates a lat and lon point can be located
    in the bounds of the WGS84 CRS, after wrapping the
    longitude value within [-180, 180]

    :param point: tuple (lat, lng)
    """
    lat, lng = point
    # Put the longitude in the range of [0,360]:
    lng %= 360
    # Put the longitude in the range of [-180,180]:
    if lng >= 180:
        lng -= 360
    lon_lat_point = SP(lng, lat)
    lon_lat_bounds = Polygon.from_bounds(
        xmin=-180.0, ymin=-90.0, xmax=180.0, ymax=90.0
    )
    # return lon_lat_bounds.intersects(lon_lat_point)
    # would not provide any corrected values

    if lon_lat_bounds.intersects(lon_lat_point):
        return True
    return False
