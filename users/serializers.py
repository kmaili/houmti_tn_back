from rest_framework import serializers
from django.core.validators import RegexValidator
from django.db import transaction
from django.db.models import Avg
from core.models import Image
from core.serializers import ImageSerializer
from districts.models import District
from districts.serializers import DistrictSerializer
from portfolio.serializers import PortfolioSerializer
from services.serializers import ServiceSerializer
from .models import Client, Artist, User

class BaseRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        fields = ['name', 'email', 'phone_number', 'password']

    @transaction.atomic
    def create(self, validated_data):
        profile_pic = validated_data.pop('profile_pic', None)
        user = self.Meta.model.objects.create_user(**validated_data)
        if profile_pic:
            Image.objects.create(image=profile_pic, user=user)
        return user

class ClientRegistrationSerializer(BaseRegistrationSerializer):
    class Meta(BaseRegistrationSerializer.Meta):
        model = Client

class ArtistRegistrationSerializer(BaseRegistrationSerializer):
    class Meta(BaseRegistrationSerializer.Meta):
        model = Artist

class BaseUserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    district = DistrictSerializer(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), source='district', write_only=True
    )
    profile_pic_binary = serializers.ImageField(
        required=False,
        write_only=True
    )
    profile_pic = ImageSerializer(read_only=True)
    unread_notifications_count = serializers.SerializerMethodField()

    def get_unread_notifications_count(self, obj):
        return obj.notifications.filter(read=False).count()
    
    class Meta:
        model = User
        fields = [
            'id', 'name', 'email', 'phone_number', 'user_type', 'is_active', 'unread_notifications_count',
            'disabled_at', 'district', 'district_id', 'profile_pic', 'profile_pic_binary', 'last_activity_at', 'coord_x', 'coord_y'
        ]

    def get_profile_pic(self, obj):
        if hasattr(obj, 'profile_pic') and obj.profile_pic and obj.profile_pic.image:
            return obj.profile_pic.image.url
        return None

    @transaction.atomic
    def update(self, instance, validated_data):
        print(validated_data)
        district = validated_data.pop('district', None)
        if district is not None:
            instance.district = district

        profile_pic_data = validated_data.pop('profile_pic_binary', None)
        if profile_pic_data:
            Image.objects.update_or_create(
                profile=instance, 
                defaults={'image': profile_pic_data}
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class ClientUserSerializer(BaseUserSerializer):
    user_type = serializers.SerializerMethodField()

    def get_user_type(self, obj):
        return "client"

class ArtistUserSerializer(BaseUserSerializer):
    user_type = serializers.SerializerMethodField()
    portfolio = PortfolioSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField()
    rate_average = serializers.SerializerMethodField()

    def get_user_type(self, obj):
        return "artisan"

    def get_is_favorite(self, obj):
        try:
            request = self.context['request']
            client = request.user.client
        except Exception:
            return False
        return client.favorites.filter(artisan=obj).exists()

    def get_rate_average(self, obj):
        avg = obj.reviews.aggregate(Avg('nb_stars'))['nb_stars__avg']
        return avg if avg is not None else 0.0


    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ['portfolio', 'service', 'is_favorite', 'rate_average']

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(
        max_length=6, 
        min_length=6,
        validators=[RegexValidator(r'^\d{6}$', 'Le code doit contenir exactement 6 chiffres.')]
    )