import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from faker import Faker

from core.models import Image
from users.models import Client, Artist
from districts.models import District
from services.models import Domain, Service, ServiceItem, WorkTime
from portfolio.models import Portfolio, PortfolioItem
from interactions.models import (
    Booking, Review, HistoEtatBooking,
    Discussion, Message
)

fake = Faker()

# =========================
# 🔥 CONFIG (HEAVY LOAD)
# =========================

NUM_CLIENTS = 500
NUM_ARTISTS = 200
BOOKINGS_PER_CLIENT = 20
DISCUSSIONS_PER_CLIENT = 50
MESSAGES_PER_DISCUSSION = (20, 100)

BATCH_SIZE = 5000


class Command(BaseCommand):
    help = "🔥 MASSIVE SEED (FIXED MULTI-TABLE INHERITANCE)"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting massive seed..."))

        districts = list(District.objects.all())

        domain_names = [
            "Plumbing", "Electricity", "Carpentry",
            "Painting", "Masonry", "Cleaning"
        ]
        domains = [Domain.objects.get_or_create(name=n)[0] for n in domain_names]

        password = make_password("password123")

        # =========================================================
        # 1. CLIENTS (❌ NO BULK - FIX FOR INHERITANCE)
        # =========================================================
        self.stdout.write(f"Creating {NUM_CLIENTS} clients...")

        clients = []
        for _ in range(NUM_CLIENTS):
            clients.append(
                Client.objects.create(
                    email=fake.unique.email(),
                    name=fake.name(),
                    phone_number=fake.phone_number()[:20],
                    password=password,
                    is_active=True,
                    district=random.choice(districts)
                )
            )

        # =========================================================
        # 2. ARTISTS (❌ NO BULK - FIX FOR INHERITANCE)
        # =========================================================
        self.stdout.write(f"Creating {NUM_ARTISTS} artists...")

        artists = []
        for _ in range(NUM_ARTISTS):
            artists.append(
                Artist.objects.create(
                    email=fake.unique.email(),
                    name=fake.name(),
                    phone_number=fake.phone_number()[:20],
                    password=password,
                    is_active=True,
                    district=random.choice(districts),
                    coord_x=float(fake.latitude()),
                    coord_y=float(fake.longitude())
                )
            )

        # =========================================================
        # 3. SERVICES + ITEMS (BULK OK)
        # =========================================================
        self.stdout.write("Creating services...")

        service_items = []

        for artist in artists:
            wt = WorkTime.objects.create(
                days="Mon-Sun",
                start_hour="08:00",
                end_hour="20:00"
            )

            service = Service.objects.create(
                artist=artist,
                domain=random.choice(domains),
                name=f"Pro {fake.job()}",
                description=fake.text(),
                work_time=wt,
                exp_years=random.randint(1, 20)
            )

            for _ in range(5):
                service_items.append(
                    ServiceItem(
                        service=service,
                        name=fake.catch_phrase(),
                        price=random.randint(20, 1000)
                    )
                )

            portfolio = Portfolio.objects.create(
                artist=artist,
                nb_views=random.randint(0, 5000)
            )

            PortfolioItem.objects.create(
                portfolio=portfolio,
                name="Main Project",
                description=fake.text()
            )

        ServiceItem.objects.bulk_create(service_items)
        service_items = list(ServiceItem.objects.all())

        # =========================================================
        # 4. BOOKINGS (BULK)
        # =========================================================
        self.stdout.write("Creating bookings...")

        bookings = []

        for client in clients:
            for _ in range(BOOKINGS_PER_CLIENT):
                item = random.choice(service_items)

                bookings.append(
                    Booking(
                        client=client,
                        service_item=item,
                        title=f"Fix {fake.word()}",
                        description=fake.sentence(),
                        address=fake.address(),
                        district=random.choice(districts)
                    )
                )

        Booking.objects.bulk_create(bookings)
        bookings = list(Booking.objects.all())

        # booking history + reviews
        histo = []
        reviews = []

        for b in bookings:
            status = random.choices(
                ["completed", "pending", "cancelled"],
                weights=[0.7, 0.2, 0.1]
            )[0]

            histo.append(HistoEtatBooking(
                booking=b,
                status=status
            ))

            if status == "completed":
                reviews.append(Review(
                    booking=b,
                    artist=b.service_item.service.artist,
                    nb_stars=random.randint(3, 5),
                    comment=fake.sentence()
                ))

        HistoEtatBooking.objects.bulk_create(histo)
        Review.objects.bulk_create(reviews)

        # =========================================================
        # 5. DISCUSSIONS
        # =========================================================
        self.stdout.write("Creating discussions...")

        discussions = []
        used_pairs = set()

        for client in clients:
            sample_artists = random.sample(
                artists,
                min(DISCUSSIONS_PER_CLIENT, len(artists))
            )

            for artist in sample_artists:
                pair = (client.id, artist.id)
                if pair in used_pairs:
                    continue

                used_pairs.add(pair)

                discussions.append(
                    Discussion(
                        client=client,
                        artist=artist
                    )
                )

        Discussion.objects.bulk_create(discussions)
        discussions = list(Discussion.objects.all())

        # =========================================================
        # 6. MESSAGES (HEAVY LOAD SIMULATION)
        # =========================================================
        self.stdout.write("Creating messages...")

        messages = []
        now = timezone.now()

        for discussion in discussions:
            count = random.randint(*MESSAGES_PER_DISCUSSION)

            participants = [
                discussion.client.id,
                discussion.artist.id
            ]

            base_time = now - timedelta(days=random.randint(1, 90))
            last_sender = None

            for i in range(count):
                sender = random.choice(participants)

                if sender == last_sender:
                    sender = participants[0] if sender == participants[1] else participants[1]

                last_sender = sender

                messages.append(
                    Message(
                        discussion=discussion,
                        message=fake.sentence(),
                        sender_id=sender,
                        viewed_by_receiver=random.random() > 0.3,
                        sent_at=base_time + timedelta(seconds=i * random.randint(20, 200))
                    )
                )

                if len(messages) >= BATCH_SIZE:
                    Message.objects.bulk_create(messages)
                    messages = []

        if messages:
            Message.objects.bulk_create(messages)

        self.stdout.write(self.style.SUCCESS("🔥 MASSIVE SEED COMPLETED SUCCESSFULLY"))