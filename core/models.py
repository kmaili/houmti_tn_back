from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Image(models.Model):
    def upload_image_path(instance, filename):
        if instance.portfolio_item:
            return f'portfolio/{instance.portfolio_item_id}/{filename}'
        elif instance.profile:
            return f'profile/{instance.profile_id}/{filename}'
        elif instance.booking:
            return f'booking/{instance.booking_id}/{filename}'
        elif instance.message:
            return f'message/{instance.message_id}/{filename}'
        return f'other/{filename}'


    portfolio_item = models.ForeignKey("portfolio.PortfolioItem", related_name='images', on_delete=models.CASCADE, null=True, blank=True)
    profile = models.OneToOneField("users.User", related_name='profile_pic', on_delete=models.CASCADE, null=True, blank=True)
    booking = models.ForeignKey('interactions.Booking', related_name='images', on_delete=models.CASCADE, null=True, blank=True)
    message = models.ForeignKey('interactions.Message', related_name= 'attachments', on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to=upload_image_path)

class Notification(models.Model):
    user = models.ForeignKey("users.User", related_name='notifications', on_delete=models.CASCADE)
    title = models.CharField(max_length=32)
    subtitle = models.CharField(max_length=255)
    type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey("type", "target_id")
    
    # Optional JSON field for extra metadata
    data = models.JSONField(blank=True, null=True)
    
    # Status
    read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)