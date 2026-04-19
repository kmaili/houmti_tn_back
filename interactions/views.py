from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.views import APIView, Response
from rest_framework.generics import ListAPIView
from rest_framework import status
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser
from core.permissions import IsArtistan, IsClient
from interactions.models import Booking, Discussion, HistoEtatBooking, Message
from interactions.paginator import DiscussionPagination
from interactions.serializers import BookingSerializer, CreateMessageSerializer, DiscussionListSerializer, JobActionSerializer, MessageSerializer
from django.db.models import Q, OuterRef, Subquery
from django.shortcuts import get_object_or_404

class BookingView(APIView):
    permission_classes = [IsClient]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=BookingSerializer,
        responses={
            201: BookingSerializer,
            400: {
                "description": "Bad Request",
                "content": {
                    "application/json": {
                        "detail": "str"
                    }
                }
            }
        },
        description="Creates a new booking with optional image uploads. The client field is automatically set to the authenticated user.",
    )
    def post(self, request, *args, **kwargs):
        serializer = BookingSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        responses={
            200: BookingSerializer(many=True),
        },
        parameters=[
            OpenApiParameter(
                name='filter',
                location=OpenApiParameter.QUERY,
                description='filter by status (pending, accepted, rejected, completed)',
                type=str,
                required=False
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        bookings_qs = request.user.client.bookings.all().order_by('-created_at')
        if request.query_params.get('filter') and request.query_params['filter'].lower() != 'all':
            filter_value = request.query_params['filter'].lower()
            if filter_value in [choice[0] for choice in HistoEtatBooking.STATUS_CHOICES]:
                bookings_qs = bookings_qs.annotate(
                    latest_status=Subquery(
                        HistoEtatBooking.objects.filter(booking=OuterRef('pk')).order_by('-changed_at').values('status')[:1]
                    )
                ).filter(latest_status=filter_value)
            else:
                return Response({"detail": f"Invalid filter value. Allowed values are: {', '.join([choice[0] for choice in HistoEtatBooking.STATUS_CHOICES])}."}, status=status.HTTP_400_BAD_REQUEST)
        bookings = bookings_qs.distinct()
        serializer = BookingSerializer(bookings, many=True, context={'request': request})
        return Response(serializer.data)


class JobView(APIView):
    permission_classes = [IsArtistan]

    @extend_schema(
        responses={
            200: BookingSerializer(many=True),
        },
        description="Retrieves all jobs (bookings) for the authenticated artisan, with optional filtering by status.",
        parameters=[
            OpenApiParameter(
                name='filter',
                location=OpenApiParameter.QUERY,
                description='filter by status (pending, accepted, rejected, completed)',
                type=str,
                required=False
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        bookings_qs = Booking.objects.filter(
            service_item__service__artist=request.user.artist
        )
        if request.query_params.get('filter') and request.query_params['filter'].lower() != 'all':
            filter_value = request.query_params['filter'].lower()
            if filter_value in [choice[0] for choice in HistoEtatBooking.STATUS_CHOICES]:
                bookings_qs = bookings_qs.annotate(
                    latest_status=Subquery(
                        HistoEtatBooking.objects.filter(booking=OuterRef('pk')).order_by('-changed_at').values('status')[:1]
                    )
                ).filter(latest_status=filter_value)
            else:
                return Response({"detail": f"Invalid filter value. Allowed values are: {', '.join([choice[0] for choice in HistoEtatBooking.STATUS_CHOICES])}."}, status=status.HTTP_400_BAD_REQUEST)
        bookings = bookings_qs.distinct()
        serializer = BookingSerializer(bookings, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        request=JobActionSerializer,
        description="Updates the status of a job (booking) for the authenticated artisan.",
        responses={
            200: {
                "description": "Success",
            },
            404: {
                "description": "Booking not found or not owned by the artisan",
            },
            400: {
                "description": "Invalid status transition or missing/invalid action field"
            }
        }
    )
    def post(self, request, pk=None, *args, **kwargs):
        booking = get_object_or_404(
            Booking,
            pk=pk,
            service_item__service__artist=request.user.artist
        )

        serializer = JobActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "detail": serializer.errors.get('action', ["Invalid data"])[0]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        action = serializer.validated_data['action']

        last_status_obj = booking.status_history.order_by('-changed_at').first()
        current_status = (
            last_status_obj.status
            if last_status_obj
            else HistoEtatBooking.PENDING_CHOICE
        )

        # ✅ STATE MACHINE
        ALLOWED_TRANSITIONS = {
            HistoEtatBooking.PENDING_CHOICE: [
                HistoEtatBooking.ACCEPTED_CHOICE,
                HistoEtatBooking.REJECTED_CHOICE,
                HistoEtatBooking.CANCELLED_CHOICE,
            ],
            HistoEtatBooking.ACCEPTED_CHOICE: [
                HistoEtatBooking.COMPLETED_CHOICE,
                HistoEtatBooking.CANCELLED_CHOICE,
            ],
            HistoEtatBooking.REJECTED_CHOICE: [],
            HistoEtatBooking.COMPLETED_CHOICE: [],
            HistoEtatBooking.CANCELLED_CHOICE: [],
        }

        # ❌ Invalid transition
        if action not in ALLOWED_TRANSITIONS.get(current_status, []):
            return Response(
                {
                    "detail": f"Cannot change status from '{current_status}' to '{action}'."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Prevent duplicate same status (important)
        if action == current_status:
            return Response(
                {"detail": "Booking is already in this status."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Save new status
        HistoEtatBooking.objects.create(
            booking=booking,
            status=action
        )

        return Response(
            {"detail": "Booking status updated successfully."},
            status=status.HTTP_200_OK
        )

class CreateMessageView(APIView):
    def post(self, request):
        serializer = CreateMessageSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            message = serializer.save()
            return Response(
                MessageSerializer(message).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DiscussionMessagesView(ListAPIView):
    serializer_class = MessageSerializer
    pagination_class = DiscussionPagination

    def get_queryset(self):
        discussion_id = self.kwargs["discussion_id"]
        return Message.objects.filter(
            discussion_id=discussion_id
        ).order_by("sent_at")



class MyDiscussionsView(ListAPIView):
    serializer_class = DiscussionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DiscussionPagination

    def get_queryset(self):
        user = self.request.user

        return Discussion.objects.filter(
            Q(client=user) | Q(artist=user)
        ).order_by("-id")
