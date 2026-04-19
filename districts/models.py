from django.db import models

from django.db import models

class District(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    boundary = models.JSONField()
    centroid_lat = models.FloatField(null=True, blank=True)
    centroid_lng = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name