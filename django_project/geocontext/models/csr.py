import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from geocontext.models.validators import key_validator
from geocontext.utilities import ServiceDefinitions

LOGGER = logging.getLogger(__name__)


class CSR(models.Model):
    """Context Service Registry"""
    key = models.CharField(
        help_text=_('Key of Context Service.'),
        blank=False,
        null=False,
        max_length=200,
        unique=True,
        validators=[key_validator],
    )

    name = models.CharField(
        help_text=_('Name of Context Service.'),
        blank=False,
        null=False,
        max_length=200,
    )

    description = models.CharField(
        help_text=_('Description of Context Service.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    url = models.CharField(
        help_text=_('URL of Context Service.'),
        blank=False,
        null=False,
        max_length=1000,
    )

    user = models.CharField(
        help_text=_('User name for accessing Context Service.'),
        blank=True,
        null=True,
        max_length=200,
    )

    password = models.CharField(
        help_text=_('Password for accessing Context Service.'),
        blank=True,
        null=True,
        max_length=200,
    )

    api_key = models.CharField(
        help_text=_(
            'API key for accessing Context Service. For PlaceName queries '
            'this is your username.'),
        blank=True,
        null=True,
        max_length=200,
    )

    query_url = models.CharField(
        help_text=_('Query URL for accessing Context Service.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    query_type = models.CharField(
        help_text=_('Query type of the Context Service.'),
        blank=False,
        null=False,
        max_length=200,
        choices=ServiceDefinitions.QUERY_TYPES,
    )

    result_regex = models.CharField(
        help_text=_('Regex to retrieve the desired value.'),
        blank=False,
        null=False,
        max_length=200,
    )

    time_to_live = models.IntegerField(
        help_text=_(
            'Time to live of Context Service to be used in caching in '
            'seconds unit.'),
        blank=True,
        null=True,
        default=604800  # 7 days
    )

    srid = models.IntegerField(
        help_text=_('The Spatial Reference ID of the service registry.'),
        blank=True,
        null=True,
        default=4326
    )

    layer_typename = models.CharField(
        help_text=_('Layer type name to get the context.'),
        blank=False,
        null=False,
        max_length=200,
    )

    service_version = models.CharField(
        help_text=_('Version of the service (e.g. WMS 1.1.0, WFS 2.0.0).'),
        blank=False,
        null=False,
        max_length=200,
    )

    provenance = models.CharField(
        help_text=_('The origin or source of the Context Service Registry.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    notes = models.TextField(
        help_text=_('Notes for the Context Service Registry.'),
        blank=True,
        null=True,
    )

    licensing = models.CharField(
        help_text=_('The licensing scheme for the Context Service Registry.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    resolution = models.IntegerField(
        help_text=_('Base data resolution of the source data in meter.'),
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.name
