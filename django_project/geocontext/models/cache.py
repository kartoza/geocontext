from datetime import datetime
import pytz

from django.utils.translation import ugettext_lazy as _
from django.contrib.gis.db import models

from geocontext.models.service import Service


class Cache(models.Model):
    """Cache Model Class."""
    srid = 3857
    name = models.CharField(
        help_text=_('Name of Cache.'),
        blank=False,
        null=False,
        max_length=200,
    )
    source_uri = models.CharField(
        help_text=_('Source URI.'),
        blank=True,
        null=True,
        max_length=1000,
    )
    geometry = models.GeometryField(
        help_text=_('Geometry associated with the value (2d, EPSG:3857).'),
        blank=True,
        null=True,
        srid=srid,
        dim=2
    )
    service = models.ForeignKey(
        Service,
        help_text=_('Service associated with the value.'),
        on_delete=models.CASCADE
    )
    value = models.CharField(
        help_text=_('The value of the service.'),
        blank=True,
        null=True,
        max_length=200,
    )
    created_time = models.DateTimeField(
        help_text=_('Date of cache entry.'),
        editable=False
    )
    expired_time = models.DateTimeField(
        help_text=_('Date when the cache expires.'),
        blank=False,
        null=False
    )

    def save(self, *args, **kwargs):
        """ On save, update created time """
        self.created = datetime.utcnow().replace(tzinfo=pytz.UTC)
        return super(Cache, self).save(*args, **kwargs)
