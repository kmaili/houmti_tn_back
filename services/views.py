from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from core.constants import BadRequestCodes
from core.permissions import IsArtistan
from services.exceptions import ServiceItemCantBeDeletedException
from services.models import Domain
from .serializers import DomainSerializer, ServiceSerializer
import logging

logger = logging.getLogger(__name__)

class ServiceView(APIView):
    permission_classes = [IsArtistan]

    @extend_schema(
        description="Creates a new service.",
        request=ServiceSerializer,
        responses={
            201: {
                "description": "Service created",
            },
            400: {
                "description": "Invalid data",
            }
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = ServiceSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        logger.info(f"Service '{service.name}' created by artist {request.user.id}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        description="Updates an existing service.",
        request=ServiceSerializer,
        responses={
            200: {
                "description": "Service updated",
            },
            404: {
                "description": "No service found",
            },
            400: {
                "description": "Invalid data",
            }
        }
    )
    def put(self, request, *args, **kwargs):
        service = getattr(request.user.artist, 'service', None)
        if service is None:
            return Response({"detail": "No service found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ServiceSerializer(service, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except ServiceItemCantBeDeletedException:
            return Response(
                {"code": BadRequestCodes.SERVICE_ITEM_CANT_BE_DELETED},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error updating service for artist {request.user.id}: {str(e)}")
            return Response(
                {"detail": "An error occurred while updating the service."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(serializer.data)

    @extend_schema(
        description="Retrieves an existing service.",
        responses={
            200: ServiceSerializer,
            404: {
                "description": "No service found",
            }
        }
    )
    def get(self, request, *args, **kwargs):
        service = getattr(request.user.artist, 'service', None)
        if service is None:
            return Response({"detail": "No service found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ServiceSerializer(service, context={'request': request})
        return Response(serializer.data)

class DomainView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Lists all domains.",
        responses={
            200: DomainSerializer(many=True),
        }
    )
    def get(self, request, *args, **kwargs):
        domains = Domain.objects.all()
        serialize = DomainSerializer(domains, many=True)
        return Response(serialize.data)