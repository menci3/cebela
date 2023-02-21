from django.db import models


class Detections(models.Model):
    date = models.DateTimeField()
    visit = models.IntegerField()
    visit_pollen = models.IntegerField()
    leave = models.IntegerField()
    leave_pollen = models.IntegerField()


class Settings(models.Model):
    source = models.CharField(max_length=300)
    weights = models.CharField(max_length=300)
    tracking_method = models.CharField(max_length=300)
    img_size_x = models.IntegerField()
    img_size_y = models.IntegerField()
    start_time = models.DateTimeField(blank=True, null=True)
    device = models.IntegerField()
