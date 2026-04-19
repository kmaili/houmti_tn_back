from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from rest_framework import serializers
from users.models import ActivationCode
from users.serializers import ArtistUserSerializer, ClientUserSerializer
from django.core.mail import send_mail
from django.template.loader import render_to_string

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = ClientUserSerializer(self.user).data if hasattr(self.user, 'client') else ArtistUserSerializer(self.user).data
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        access = AccessToken(data['access'])
        user = User.objects.get(id=access['user_id'])
        data['user'] = ClientUserSerializer(user).data if hasattr(user, 'client') else ArtistUserSerializer(user).data
        return data


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        data['user'] = user
        return data

    def save(self):
        user = self.validated_data['user']
        if user.can_send_otp():
            otp = ActivationCode.generate_code()
            ActivationCode.objects.create(user=user, code=otp)

            html_message = render_to_string('otp_email.html', {'code': otp, 'name': user.name})
            send_mail(
                subject="Votre code de validation Houmti",
                message="",
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

        return {"message": "OTP sent"}

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=6)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        activation = ActivationCode.objects.filter(
            user=user,
            code=data['otp'],
            is_used=False
        ).first()

        if not activation:
            raise serializers.ValidationError("Invalid OTP")

        if activation.is_expired():
            raise serializers.ValidationError("OTP expired")

        data['user'] = user
        data['activation'] = activation
        return data

    def save(self):
        user = self.validated_data['user']
        activation = self.validated_data['activation']

        user.set_password(self.validated_data['new_password'])
        user.save()

        activation.is_used = True
        activation.save()

        return {"message": "Password updated successfully"}
