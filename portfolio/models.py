from django.db import models
from users.models import Artist, User

class Portfolio(models.Model):
    artist = models.OneToOneField(Artist, on_delete=models.CASCADE, related_name='portfolio')
    date_creation = models.DateTimeField(auto_now_add=True)
    nb_views = models.PositiveIntegerField(default=0)

class PortfolioItem(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    description = models.TextField()
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
