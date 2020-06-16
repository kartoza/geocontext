from datetime import datetime
import pytz

from django.utils.translation import ugettext_lazy as _
from django.contrib.gis.db import models


class Query(models.Model):
    """ Model to log queries to geocontext """
    query_type = models.CharField(
        help_text=_('Type of query (Service / Group / Collection'),
        blank=False,
        null=False,
        max_length=200,
    )
    key = models.CharField(
        help_text=_('Query key (service_key, group_key, collection_key)'),
        blank=False,
        null=False,
        max_length=200,
    )
    geometry = models.GeometryField(
        help_text=_('Queried point.'),
        blank=False,
        null=False,
        dim=2
    )
    tolerance = models.FloatField(
        help_text=_('Query tolerance.'),
        blank=True,
        null=True,
    )
    created_time = models.DateTimeField(
        help_text=_('Date of query.'),
        editable=False
    )

    def save(self, *args, **kwargs):
        """ On save, update created time """
        self.created_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
        return super(Query, self).save(*args, **kwargs)
