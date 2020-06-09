import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from geocontext.models.validators import key_validator
from geocontext.utilities import ServiceDefinitions

LOGGER = logging.getLogger(__name__)


class Service(models.Model):
    key = models.CharField(
        help_text=_('Key of Service.'),
        blank=False,
        null=False,
        max_length=200,
        unique=True,
        validators=[key_validator],
    )

    name = models.CharField(
        help_text=_('Name of Service.'),
        blank=False,
        null=False,
        max_length=200,
    )

    description = models.CharField(
        help_text=_('Description of Service.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    url = models.CharField(
        help_text=_('URL of Service.'),
        blank=False,
        null=False,
        max_length=1000,
    )

    user = models.CharField(
        help_text=_('User name for accessing Service.'),
        blank=True,
        null=True,
        max_length=200,
    )

    password = models.CharField(
        help_text=_('Password for accessing Service.'),
        blank=True,
        null=True,
        max_length=200,
    )

    api_key = models.CharField(
        help_text=_(
            'API key for accessing Service.'),
        blank=True,
        null=True,
        max_length=200,
    )

    query_url = models.CharField(
        help_text=_('Query URL for accessing Service.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    query_type = models.CharField(
        help_text=_('Query type of the Service.'),
        blank=False,
        null=False,
        max_length=200,
        choices=ServiceDefinitions.QUERY_TYPES,
    )

    result_regex = models.CharField(
        help_text=_(
            'Regex to retrieve the desired value. Can be the data layer name. '
            'For geoserver it may be "workspace:layer_name"'),
        blank=False,
        null=False,
        max_length=200,
    )

    layer_typename = models.CharField(
        help_text=_(
            'Layer type name to get the service. '
            'For geoserver it may be "namespace:featuretype"'),
        blank=False,
        null=False,
        max_length=200,
    )

    time_to_live = models.IntegerField(
        help_text=_(
            'Refresh timeof the service in seconds - determines Cache persistence'),
        blank=True,
        null=True,
        default=604800  # 7 days
    )

    srid = models.IntegerField(
        help_text=_('The Spatial Reference ID of the service.'),
        blank=True,
        null=True,
        default=4326
    )

    search_dist = models.FloatField(
        help_text=_(
            'Search distance around query point in meters. Helpful for non-polygon '
            'features. Also determines cache hit range for rasters'),
        blank=True,
        null=True
    )

    service_version = models.CharField(
        help_text=_('Version of the service (e.g. WMS 1.1.0, WFS 2.0.0).'),
        blank=False,
        null=False,
        max_length=200,
    )

    provenance = models.CharField(
        help_text=_('The origin or source of the Service.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    notes = models.TextField(
        help_text=_('Notes for the Service.'),
        blank=True,
        null=True,
    )

    licensing = models.CharField(
        help_text=_('The licensing scheme for the Service.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.name
