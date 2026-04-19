from shapely import Point
from shapely.geometry import shape
from districts.models import District

def _distance(lat1, lon1, lat2, lon2):
    return (lat1 - lat2)**2 + (lon1 - lon2)**2  # fast approximation


def get_user_district_optimized(lat, lng):
    districts = list(District.objects.all())

    # sort by nearest centroid first
    districts.sort(
        key=lambda d: _distance(lat, lng, d.centroid_lat, d.centroid_lng)
    )

    point = Point(lng, lat)

    for d in districts[:5]:  # check only closest 5
        polygon = shape(d.boundary)
        if polygon.contains(point):
            return d

    return None