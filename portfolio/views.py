from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from core.permissions import IsArtistan
from portfolio.models import Portfolio, PortfolioItem
from portfolio.serializers import PortfolioItemSerializer, PortfolioSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
import logging

logger = logging.getLogger(__name__)



class PortfolioItemView(APIView):
    permission_classes = [IsArtistan]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        description="Returns all items in the portfolio.",
        responses={
            200: PortfolioItemSerializer(many=True),
            404: {"description": "Artist has no portfolio"},
        }
    )
    def get(self, request, *args, **kwargs):
        portfolio, _ = Portfolio.objects.get_or_create(
            artist=request.user.artist
        )
        serializer = PortfolioSerializer(instance=portfolio)
        return Response(serializer.data)


    @extend_schema(
        description="Adds an item to the portfolio.",
        request=PortfolioItemSerializer,
        responses={
            201:  PortfolioItemSerializer,
            400: {"description": "Failed to add item to portfolio"},
        }
    )
    def post(self, request, *args, **kwargs):
        portfolio, _ = Portfolio.objects.get_or_create(
            artist=request.user.artist
        )

        serializer = PortfolioItemSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(portfolio=portfolio)
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


class PortfolioItemDetailView(APIView):
    permission_classes = [IsArtistan]

    @extend_schema(
        description="Retrieves an item from the portfolio.",
        responses={
            200: PortfolioItemSerializer,
            404: {"description": "Item not found in portfolio"},
            400: {"description": "Item ID is required."},
        }
    )
    def get(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response(
                {"detail": "Item ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user

        item = get_object_or_404(
            PortfolioItem,
            pk=pk,
            portfolio__artist=user.artist
        )

        serializer = PortfolioItemSerializer(instance=item)

        return Response(serializer.data)

    @extend_schema(
        description="Updates an item in the portfolio.",
        request=PortfolioItemSerializer,
        responses={
            200: {
                "description": "Item updated in portfolio",
            },
            404: {"description": "Item not found in portfolio"},
            400: {"description": "Failed to update item in portfolio"},
        }
    )
    def put(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response(
                {"detail": "Item ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user

        item = get_object_or_404(
            PortfolioItem,
            pk=pk,
            portfolio__artist=user.artist
        )

        serializer = PortfolioItemSerializer(instance=item, data=request.data)

        if serializer.is_valid():
            serializer.save()
            logging.info("Item updated in portfolio")
            return Response(serializer.data, status=status.HTTP_200_OK)

        logging.error(f"Failed to update item in portfolio, errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Deletes an item from the portfolio.",
        responses={
            204: {"description": "Item deleted from portfolio"},
            404: {"description": "Item not found in portfolio"},
        }
    )
    def delete(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response(
                {"detail": "Item ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user

        print(user.artist)
        item = get_object_or_404(
            PortfolioItem,
            pk=pk,
            portfolio__artist=user.artist
        )

        item.delete()
        logging.info("Item deleted from portfolio")
        return Response(status=status.HTTP_204_NO_CONTENT)