from django.db import models
from users.models import Client, Artist
from services.models import ServiceItem

class Booking(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='bookings')
    service_item = models.ForeignKey(ServiceItem, on_delete=models.CASCADE, related_name='bookings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    start_at = models.DateTimeField(null=True, blank=True)
    district = models.ForeignKey('districts.District', on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)

class HistoEtatBooking(models.Model):
    PENDING_CHOICE = 'pending'
    ACCEPTED_CHOICE = 'accepted'
    REJECTED_CHOICE = 'rejected'
    COMPLETED_CHOICE = 'completed'
    CANCELLED_CHOICE = 'cancelled'
    STATUS_CHOICES = [
        (PENDING_CHOICE, 'Pending'),
        (ACCEPTED_CHOICE, 'Accepted'),
        (REJECTED_CHOICE, 'Rejected'),
        (COMPLETED_CHOICE, 'Completed'),
        (CANCELLED_CHOICE, 'Cancelled'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=PENDING_CHOICE)
    changed_at = models.DateTimeField(auto_now_add=True)

class Discussion(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)

class Message(models.Model):
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    sender_id = models.IntegerField()
    viewed_by_receiver = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='reviews')
    nb_stars = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)