from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from django.contrib.contenttypes.models import ContentType
from core.models import Notification
from core.permissions import IsClient
from core.serializers import Notificationserializer
from interactions.models import Booking
from interactions.recommender import ArtisanRecommender
from users.notif_paginator import UserNotificationPagination
from users.paginator import ArtisanPagination
from .serializers import ArtistUserSerializer, ClientRegistrationSerializer, ArtistRegistrationSerializer, ClientUserSerializer, VerifyOTPSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ActivationCode, Artist, Favorite, User
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
import logging

logger = logging.getLogger(__name__)

class ClientRegisterView(generics.CreateAPIView):
    serializer_class = ClientRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class ArtistRegisterView(generics.CreateAPIView):
    serializer_class = ArtistRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        user = get_object_or_404(User, pk=pk) if pk else request.user

        if hasattr(user, 'client'):
            serializer = ClientUserSerializer(user.client)
        else:
            serializer = ArtistUserSerializer(user.artist)

        return Response(serializer.data)
    
    def put(self, request, *args, **kwargs):
        user = request.user
        serializer_class = ClientUserSerializer if hasattr(user, 'client') else ArtistUserSerializer
        serializer = serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = []

    @extend_schema(
        auth=[],
        description="Activates the user account and returns JWT tokens if the OTP is valid.",
        request=VerifyOTPSerializer,
        responses={
            200: {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "access": "str",
                        "refresh": "str",
                        "user": {
                            "name": "str",
                            "email": "str",
                            "user_type": "str",
                            "is_active": "bool",
                            "disabled_at": "datetime",
                            "district": "str"
                        }
                    }
                }
            },
            400: {"description": "Invalid or expired code"}
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        # Find the latest unused code for this user
        activation = ActivationCode.objects.filter(
            user__email=email, 
            code=otp, 
            is_used=False
        ).first()

        if not activation or activation.is_expired():
            return Response(
                {"error": "Code invalide ou expiré."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        with transaction.atomic():
            # 1. Activate the User
            user = activation.user
            user.is_active = True
            user.save()

            # 2. Mark code as used
            activation.is_used = True
            activation.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": ClientUserSerializer(user).data if hasattr(user, 'client') else ArtistUserSerializer(user).data
        
        }, status=status.HTTP_200_OK)


class UserNotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='page', description='Page number', required=False, type=int),
            OpenApiParameter(name='page_size', description='Number of notifications per page', required=False, type=int),
        ],
        responses={200: Notificationserializer(many=True)},
        description="Retrieves paginated notifications for the authenticated user."
    )
    def get(self, request, *args, **kwargs):
        queryset = request.user.notifications.all().order_by('-created_at')  # newest first

        paginator = UserNotificationPagination()
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = Notificationserializer(paginated_qs, many=True)

        return paginator.get_paginated_response(serializer.data)
    
    @extend_schema(
        request=None,
        responses={200: {"description": "Notifications marked as read"}},
        description="Marks all notifications for the authenticated user as read."
    )
    def post(self, request, pk=None, *args, **kwargs):
        if pk:
            notification = get_object_or_404(Notification, pk=pk, user=request.user)
            notification.read = True
            notification.save(update_fields=['read'])
            logger.info(f"User {request.user.id} marked notification {notification.id} as read.")
            return Response({"detail": "Notification marked as read"}, status=status.HTTP_200_OK)
        
        request.user.notifications.filter(read=False).update(read=True)
        logger.info(f"User {request.user.id} marked all notifications as read.")
        return Response({"detail": "Notifications marked as read"}, status=status.HTTP_200_OK)



class ArtisanSearch(APIView):
    permission_classes = [IsClient]
    pagination_class = ArtisanPagination

    @extend_schema(
        parameters=[
            OpenApiParameter(name='q', description='Search query', required=False, type=str),
            OpenApiParameter(name='page', description='Page number', required=False, type=int),
            OpenApiParameter(name='limit', description='Items per page', required=False, type=int),
        ],
        responses={200: ArtistUserSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):

        query = request.query_params.get("q")

        recommender = ArtisanRecommender()
        queryset = recommender.recommend_artisans(
            client=request.user.client,
            query=query
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        serializer = ArtistUserSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


class Favorites(APIView):
    permission_classes = [IsClient]
    pagination_class = ArtisanPagination

    @extend_schema(
        parameters=[
            OpenApiParameter(name='q', description='Search query', required=False, type=str),
            OpenApiParameter(name='page', description='Page number', required=False, type=int),
            OpenApiParameter(name='limit', description='Items per page', required=False, type=int),
        ],
        responses={200: ArtistUserSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q")

        queryset = (
            Artist.objects
            .filter(favorites__client=request.user.client)
            .order_by('-favorites__created_at')
            .distinct()
        )

        if query:
            queryset = queryset.filter(name__icontains=query)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        serializer = ArtistUserSerializer(page, many=True, context={'request': request})

        return paginator.get_paginated_response(serializer.data)


    @extend_schema(
        summary="Add artisan to favorites",
        description="Allows a client to add an artisan to their favorites list. If already favorited, returns a safe response without duplication.",
        request={
            "type": "object",
            "properties": {
                "artisan_id": {
                    "type": "integer",
                    "example": 12
                }
            },
            "required": ["artisan_id"]
        },
        responses={
            201: OpenApiResponse(
                description="Successfully added to favorites",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "detail": "Added to favorites",
                            "artisan_id": 12
                        }
                    )
                ],
            ),
            200: OpenApiResponse(
                description="Already exists in favorites",
                examples=[
                    OpenApiExample(
                        "Already exists",
                        value={
                            "detail": "Already in favorites"
                        }
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Invalid request",
                examples=[
                    OpenApiExample(
                        "Missing artisan_id",
                        value={
                            "detail": "artisan_id is required"
                        }
                    )
                ],
            ),
            404: OpenApiResponse(
                description="Artisan not found",
                examples=[
                    OpenApiExample(
                        "Not found",
                        value={
                            "detail": "Not found"
                        }
                    )
                ],
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        artisan_id = request.data.get("artisan_id")

        if not artisan_id:
            return Response(
                {"detail": "artisan_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        artisan = get_object_or_404(Artist, id=artisan_id)

        favorite, created = Favorite.objects.get_or_create(
            artisan=artisan,
            client=request.user.client
        )

        if not created:
            return Response(
                {"detail": "Already in favorites"},
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "detail": "Added to favorites",
                "artisan_id": artisan.id
            },
            status=status.HTTP_201_CREATED
        )
    
    @extend_schema(
        summary="Remove artisan from favorites",
        responses={
            200: OpenApiResponse(
                description="Removed successfully",
                examples=[
                    OpenApiExample(
                        "Removed",
                        value={
                            "detail": "Removed from favorites",
                            "artisan_id": 12,
                            "favorited": False
                        }
                    )
                ],
            ),
            404: OpenApiResponse(
                description="Not found",
            ),
        },
    )
    def delete(self, request, *args, **kwargs):
        artisan_id = request.data.get("artisan_id")

        if not artisan_id:
            return Response(
                {"detail": "artisan_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite = Favorite.objects.filter(
            artisan_id=artisan_id,
            client=request.user.client
        )

        if not favorite.exists():
            return Response(
                {"detail": "Not in favorites"},
                status=status.HTTP_404_NOT_FOUND
            )

        favorite.delete()

        return Response(
            {
                "detail": "Removed from favorites",
                "artisan_id": artisan_id,
                "favorited": False
            },
            status=status.HTTP_200_OK
        )
