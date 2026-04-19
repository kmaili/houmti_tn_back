from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import ActivationCode, Client, Artist
from django.template.loader import render_to_string

@receiver(post_save, sender=Client)
@receiver(post_save, sender=Artist)
def send_otp_on_registration(sender, instance, created, **kwargs):
    if created and not instance.is_active:
        # Check rate limit before sending
        if instance.can_send_otp():
            otp = ActivationCode.generate_code()
            ActivationCode.objects.create(user=instance, code=otp)

            html_message = render_to_string('otp_email.html', {'code': otp, 'name': instance.name})
            send_mail(
                subject="Votre code de validation Houmti",
                message="",
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
            )