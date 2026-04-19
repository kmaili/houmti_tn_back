from django.db import models
from users.models import Artist

class Domain(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='domains/')

class Service(models.Model):
    artist = models.OneToOneField(Artist, on_delete=models.CASCADE, related_name='service')
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    work_time = models.OneToOneField("WorkTime", on_delete=models.CASCADE, related_name='service', null=True, blank=True)
    exp_years = models.PositiveIntegerField()

class ServiceItem(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class WorkTime(models.Model):
    days = models.CharField(max_length=100)
    start_hour = models.TimeField()
    end_hour = models.TimeField()