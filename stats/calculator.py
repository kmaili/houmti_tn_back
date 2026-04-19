from django.db.models import Avg, Count
from django.utils import timezone

from users.models import Artist
from interactions.models import Booking, Review, HistoEtatBooking
from stats.models import ArtistStats


class ArtistStatsBuilder:

    def rebuild_all(self):

        for artist in Artist.objects.all().iterator():

            reviews = Review.objects.filter(artist=artist)
            bookings = Booking.objects.filter(service_item__service__artist=artist)

            total = bookings.count()
            completed = HistoEtatBooking.objects.filter(
                booking__in=bookings,
                status="completed"
            ).count()

            cancelled = HistoEtatBooking.objects.filter(
                booking__in=bookings,
                status="cancelled"
            ).count()

            avg_rating = reviews.aggregate(avg=Avg("nb_stars"))["avg"] or 0
            review_count = reviews.count()

            reliability = (
                (0.7 * (completed / total if total else 0))
                + (0.3 * (1 - (cancelled / total if total else 0)))
            ) if total else 0

            popularity = min(total / 50, 1)

            last_booking = bookings.order_by("-created_at").first()

            ArtistStats.objects.update_or_create(
                artist=artist,
                defaults={
                    "avg_rating": avg_rating,
                    "review_count": review_count,
                    "total_bookings": total,
                    "completed_bookings": completed,
                    "cancelled_bookings": cancelled,
                    "reliability_score": reliability,
                    "popularity_score": popularity,
                    "last_booking_at": getattr(last_booking, "created_at", None),
                }
            )