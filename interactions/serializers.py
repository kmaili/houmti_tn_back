from rest_framework import serializers
from django.db import transaction
from core.models import Image
from core.serializers import ImageSerializer
from districts.models import District
from districts.serializers import DistrictSerializer
from interactions.models import Booking, Discussion, HistoEtatBooking, Message, Review
from services.models import ServiceItem
from services.serializers import ServiceItemSerializer
from users.models import User
from users.serializers import ArtistUserSerializer, ClientUserSerializer

class BookingSerializer(serializers.ModelSerializer):
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        source='client',
        write_only=True,
        default=serializers.CurrentUserDefault()  # placeholder, we'll override it
    )
    client = ClientUserSerializer(read_only=True)
    artisan = ArtistUserSerializer(source='service_item.service.artist', read_only=True)
    images_upload = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    images = ImageSerializer(many=True, read_only=True)
    service_item = ServiceItemSerializer(read_only=True)
    service_item_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceItem.objects.all(), source='service_item', write_only=True
    )
    district = DistrictSerializer(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), source='district', write_only=True
    )
    status = serializers.SerializerMethodField(read_only=True)

    def get_default_client(self):
        request = self.context.get('request')
        if request and hasattr(request.user, 'client'):
            return request.user.client
        return None

    def get_status(self, obj):
        return obj.status_history.order_by('-changed_at').first().status if obj.status_history.exists() else HistoEtatBooking.PENDING_CHOICE
    class Meta:
        model = Booking
        fields = '__all__'
    

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['client'] = user.client

        images_files = validated_data.pop('images_upload', [])
        Booking_obj = Booking.objects.create(**validated_data)
        
        for img_file in images_files:
            Image.objects.create(booking=Booking_obj, image=img_file)
        
        return Booking_obj

class JobActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=[choice[0] for choice in HistoEtatBooking.STATUS_CHOICES])

class MessageSerializer(serializers.ModelSerializer):
    attachments = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "message",
            "sender_id",
            "viewed_by_receiver",
            "sent_at",
            "attachments",
        ]

class CreateMessageSerializer(serializers.Serializer):
    receiver_id = serializers.IntegerField()
    message = serializers.CharField()
    images_upload = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    @transaction.atomic
    def create(self, validated_data):
        sender_id = self.context["request"].user.id
        receiver_id = validated_data["receiver_id"]
        message_text = validated_data["message"]
        images = validated_data.get("images_upload", [])

        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)

        # get or create discussion
        sender_client = getattr(sender, 'client', None)
        receiver_client = getattr(receiver, 'client', None)

        sender_artist = getattr(sender, 'artist', None)
        receiver_artist = getattr(receiver, 'artist', None)

        # Perform the get_or_create
        discussion, created = Discussion.objects.get_or_create(
            client=sender_client or receiver_client,
            artist=sender_artist or receiver_artist
        )

        # create message
        message = Message.objects.create(
            discussion=discussion,
            message=message_text,
            sender_id=sender_id
        )

        # attach images
        print("Received images:", images)  # Debugging statement
        for img in images:
            Image.objects.create(
                message=message,
                image=img
            )

        return message


class ReviewSerializer(serializers.ModelSerializer):
    bookingId = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.all(), source='booking', write_only=True
    )
    client = ClientUserSerializer(source='booking.client', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'bookingId', 'nb_stars', 'comment', 'created_at', 'client']
        read_only_fields = ['id', 'created_at', 'client']

    def validate_nb_stars(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Stars must be between 1 and 5.")
        return value

    def validate(self, data):
        booking = data.get('booking')
        user = self.context['request'].user

        if self.instance:
            # During update, booking shouldn't be changed if it was provided
            if booking and booking != self.instance.booking:
                raise serializers.ValidationError("Cannot change the booking of a review.")
            return data

        # Check if booking belongs to the client
        if not hasattr(user, 'client') or booking.client != user.client:
            raise serializers.ValidationError("You can only rate your own bookings.")

        # Check if booking is completed
        last_status = booking.status_history.order_by('-changed_at').first()
        if not last_status or last_status.status != HistoEtatBooking.COMPLETED_CHOICE:
            raise serializers.ValidationError("You can only rate completed bookings.")

        # Check if review already exists
        if hasattr(booking, 'review'):
            raise serializers.ValidationError("This booking has already been rated.")

        return data

    def create(self, validated_data):
        booking = validated_data['booking']
        validated_data['artist'] = booking.service_item.service.artist
        return super().create(validated_data)


class DiscussionListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    client = ClientUserSerializer(read_only=True)
    artist = ArtistUserSerializer(read_only=True)

    class Meta:
        model = Discussion
        fields = [
            "id",
            "client",
            "artist",
            "last_message",
            "unread_count",
        ]

    def get_last_message(self, obj):
        message = obj.messages.order_by("-sent_at").first()
        if message:
            return MessageSerializer(message, context=self.context).data
        return None

    def get_unread_count(self, obj):
        user_id = self.context["request"].user.id

        return obj.messages.filter(
            viewed_by_receiver=False
        ).exclude(sender_id=user_id).count()
