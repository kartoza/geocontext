from datetime import datetime
import pytz

from django.contrib.gis.db import models


class Log(models.Model):
    """ Model to log queries to geocontext """
    registry = models.CharField(
        help_text=('Registry that was queried'),
        blank=False,
        null=False,
        max_length=200,
    )
    key = models.CharField(
        help_text=('Query key'),
        blank=False,
        null=False,
        max_length=200,
    )
    geometry = models.GeometryField(
        help_text=('Queried point.'),
        blank=False,
        null=False,
        dim=2
    )
    tolerance = models.FloatField(
        help_text=('Query tolerance.'),
        blank=True,
        null=True,
    )
    output_format = models.CharField(
        help_text=('Format requested'),
        blank=False,
        null=False,
        max_length=200,
    )
    created_time = models.DateTimeField(
        help_text=('Date of query.'),
        editable=False
    )

    def save(self, *args, **kwargs):
        """ On save, update created time """
        self.created_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
        return super(Log, self).save(*args, **kwargs)
