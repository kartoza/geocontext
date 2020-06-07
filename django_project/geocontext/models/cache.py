from django.utils.translation import ugettext_lazy as _
from django.contrib.gis.db import models

from geocontext.models.csr import CSR


class Cache(models.Model):
    """Context Cache Model Class."""

    name = models.CharField(
        help_text=_('Name of Cache Context.'),
        blank=False,
        null=False,
        max_length=200,
    )
    source_uri = models.CharField(
        help_text=_('Source URI of the Context.'),
        blank=True,
        null=True,
        max_length=1000,
    )
    geometry = models.GeometryField(
        help_text=_(
            'Geometry associated with the value. In the same srid as the service.'),
        blank=True,
        null=True,
        dim=3
    )
    csr = models.ForeignKey(
        CSR,
        help_text=_('Service registry associated with the value.'),
        on_delete=models.CASCADE
    )
    value = models.CharField(
        help_text=_('The value of the registry.'),
        blank=True,
        null=True,
        max_length=200,
    )
    expired_time = models.DateTimeField(
        help_text=_('Date when the cache expires.'),
        blank=False,
        null=False
    )
