from django.db import models
from users.models import Artist


class ArtistStats(models.Model):
    artist = models.OneToOneField(
        Artist,
        on_delete=models.CASCADE,
        related_name="stats"
    )

    # review
    avg_rating = models.FloatField(default=0)
    review_count = models.IntegerField(default=0)

    # bookings
    total_bookings = models.IntegerField(default=0)
    completed_bookings = models.IntegerField(default=0)
    cancelled_bookings = models.IntegerField(default=0)

    # activity
    last_booking_at = models.DateTimeField(null=True, blank=True)

    # precomputed derived metrics
    reliability_score = models.FloatField(default=0)
    popularity_score = models.FloatField(default=0)

    updated_at = models.DateTimeField(auto_now=True)