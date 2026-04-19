from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from districts.helpers import get_user_district_optimized
from districts.models import District
from districts.serializers import DistrictSerializer


class DisctrictView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = District.objects.all()
    serializer_class = DistrictSerializer

class UserDistrictView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Get user's district based on location",
        parameters=[
            OpenApiParameter(
                name='lat',
                description='Latitude',
                required=True,
                type=float,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='lng',
                description='Longitude',
                required=True,
                type=float,
                location=OpenApiParameter.QUERY
            ),
        ],
        responses={
            200: DistrictSerializer,
            404: {"description": "No district found"},
        }
    )
    def get(self, request, *args, **kwargs):
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response({"detail": "Invalid latitude or longitude."}, status=400)

        district = get_user_district_optimized(lat, lng)
        return Response(DistrictSerializer(district).data, status=200) if district else Response({"detail": "No district found."}, status=404)