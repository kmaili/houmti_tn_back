import json
from django.core.management.base import BaseCommand
from shapely.geometry import shape, Polygon, LineString
from districts.models import District
import re

BIDI_CHARS = re.compile(r'[\u202A-\u202E\u200E\u200F]')

def clean_text(text: str) -> str:
    if not text:
        return text
    
    text = BIDI_CHARS.sub('', text)
    return text.strip()

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        District.objects.all().delete()
        with open('municipalites.geojson') as f:
            data = json.load(f)

        objs = []

        for feature in data['features']:
            props = feature.get('properties', {})

            name = clean_text(
                props.get('name:fr')
                or props.get('name')
                or props.get('@relations', [{}])[0]
                    .get('reltags', {})
                    .get('name:fr')
                or props.get('@relations', [{}])[0]
                    .get('reltags', {})
                    .get('name')
                or "UNKNOWN"
            )

            geom = shape(feature['geometry'])

            if isinstance(geom, LineString):
                coords = list(geom.coords)
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                geom = Polygon(coords)

            if not geom.is_valid:
                continue  # skip broken ones (important)

            centroid = geom.centroid
            print(name)
            objs.append(District(
                name=name,
                boundary=geom.__geo_interface__,
                centroid_lat=centroid.y,
                centroid_lng=centroid.x
            ))

        seen = set()
        objs = [obj for obj in objs if obj.name not in seen and not seen.add(obj.name)]
        District.objects.bulk_create(objs, batch_size=200)