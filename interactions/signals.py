from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Notification
from interactions.models import Booking, HistoEtatBooking, Message, Discussion
from django.contrib.contenttypes.models import ContentType
import logging
from users.models import Artist, Client

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Message)
def notify_unread_messages(sender, instance, created, **kwargs):
    if created:
        discussion = instance.discussion
        # Count consecutive unread messages from the same sender
        unread_count = discussion.messages.filter(viewed_by_receiver=False, sender_id=instance.sender_id).count()
        
        # Check if we have exactly 5 unread messages to avoid spamming
        if unread_count >= 5:
            # Determine the receiver
            if instance.sender_id == discussion.client.id:
                receiver_user = discussion.artist
                sender_name = discussion.client.name
            else:
                receiver_user = discussion.client
                sender_name = discussion.artist.name
            
            Notification.objects.create(
                user=receiver_user,
                title=f"New messages from {sender_name}",
                subtitle=f"You have {unread_count} unread messages from {sender_name}. Click to view.",
                type=ContentType.objects.get_for_model(Discussion),
                target_id=discussion.id
            )
            logger.info(f"Unread messages notification sent to user {receiver_user.id} for discussion {discussion.id}")

@receiver(post_save, sender=Booking)
def init_booking_history(sender, instance, created, **kwargs):
    if created:
        HistoEtatBooking.objects.create(booking=instance, status=HistoEtatBooking.PENDING_CHOICE)
        logger.info(f"Booking history initialized for booking ID: {instance.id}")
        client: Client = instance.client
        artisan: Artist = instance.service_item.service.artist
        Notification.objects.create(
            user=artisan,
            title="New booking request received.",
            subtitle=f"{client.name} has requested a booking for {instance.service_item.name}, click to view details.",
            type=ContentType.objects.get_for_model(Booking),
            target_id=instance.id
        )
        logger.info(f"Notification created for booking ID: {instance.id} and user ID: {client.id}")

@receiver(post_save, sender=HistoEtatBooking)
def notify_booking_status_change(sender, instance, created, **kwargs):
    if created and instance.status != HistoEtatBooking.PENDING_CHOICE:
        booking = instance.booking
        client: Client = booking.client
        artisan: Artist = booking.service_item.service.artist
        status_message = {
            HistoEtatBooking.PENDING_CHOICE: "pending",
            HistoEtatBooking.ACCEPTED_CHOICE: "accepted",
            HistoEtatBooking.REJECTED_CHOICE: "rejected",
            HistoEtatBooking.COMPLETED_CHOICE: "completed",
            HistoEtatBooking.CANCELLED_CHOICE: "canceled"
        }.get(instance.status, "updated")
        if status_message in ['accepted', 'rejected', 'completed']: # notify the client

            Notification.objects.create(
                user=client,
                title=f"Your booking has been {status_message}.",
                subtitle=f"{artisan.name} has {status_message} your booking for {booking.service_item.name}, click to view details.",
                type=ContentType.objects.get_for_model(Booking),
                target_id=booking.id
            )
        else: # notify the artisan
            Notification.objects.create(
                user=artisan,
                title=f"A booking has been {status_message}.",
                subtitle=f"{client.name} has {status_message} a booking for {booking.service_item.name}, click to view details.",
                type=ContentType.objects.get_for_model(Booking),
                target_id=booking.id
            )
        logger.info(f"Notification created for booking ID: {booking.id} with status: {status_message}")