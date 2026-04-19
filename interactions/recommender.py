from typing import Optional, List

from django.db.models import (
    Case, When, Value, FloatField, F, ExpressionWrapper
)
from django.db.models.functions import Coalesce

from users.models import Artist
from stats.models import ArtistStats


class ArtisanRecommender:

    # =========================
    # PUBLIC METHOD
    # =========================

    def recommend_artisans(self, client, query: Optional[str] = None):

        qs = Artist.objects.filter(is_active=True).select_related(
            "service", "service__domain", "stats"
        ).annotate(

            quality=Coalesce(F("stats__avg_rating") / 5.0, 0.5),
            reliability=Coalesce(F("stats__reliability_score"), 0.5),
            popularity=Coalesce(F("stats__popularity_score"), 0.0),

            review_boost=Case(
                When(stats__review_count__gte=10, then=Value(1.0)),
                When(stats__review_count__gte=3, then=Value(0.7)),
                default=Value(0.4),
                output_field=FloatField()
            ),

            relevance=Case(
                When(service__domain__name__icontains=query or "", then=Value(1.0)),
                When(service__name__icontains=query or "", then=Value(0.8)),
                When(service__description__icontains=query or "", then=Value(0.6)),
                default=Value(0.3),
                output_field=FloatField()
            ),

            freshness=Case(
                When(stats__last_booking_at__isnull=True, then=Value(0.5)),
                default=Value(0.2),
                output_field=FloatField()
            ),
        )

        client_domain = self._get_client_domain(client)
        client_district = client.district_id

        qs = qs.annotate(
            final_score=(
                (
                    0.40 * F("relevance") +
                    0.20 * F("quality") +
                    0.15 * F("reliability") +
                    0.10 * F("review_boost") +
                    0.08 * F("popularity") +
                    0.07 * F("freshness")
                )
                if query else
                (
                    0.25 * F("quality") +
                    0.20 * F("reliability") +
                    0.35 * Value(self._client_affinity_score(client, client_domain, client_district)) +
                    0.10 * F("popularity") +
                    0.10 * F("freshness")
                )
            )
        ).order_by("-final_score")

        return qs  # ✅ NO slicing, NO list()
    # =========================
    # CLIENT AFFINITY (LIGHTWEIGHT)
    # =========================

    def _client_affinity_score(self, client, domain, district):

        # ultra lightweight precomputed-style heuristic
        score = 0.0

        if domain:
            score += 0.5

        if district:
            score += 0.3

        # you can extend later with cached tables
        return min(score, 1.0)

    def _get_client_domain(self, client):
        from services.models import Service

        return (
            Service.objects
            .filter(items__bookings__client=client)
            .values_list("domain_id", flat=True)
            .first()
        )