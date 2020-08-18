import logging

from django.contrib.auth.models import Group as AuthGroup
from django.db import models
from django.utils.translation import ugettext_lazy as _

from geocontext.models.validators import key_validator

LOGGER = logging.getLogger(__name__)


class Service(models.Model):
    WFS = 'WFS'
    WCS = 'WCS'
    WMS = 'WMS'
    REST = 'REST'
    ARCREST = 'ArcREST'
    WIKIPEDIA = 'Wikipedia'
    PLACENAME = 'PlaceName'
    QUERY_TYPES = (
        (WFS, 'WFS'),
        (WCS, 'WCS'),
        (WMS, 'WMS'),
        (REST, 'REST'),
        (ARCREST, 'ArcREST'),
        (WIKIPEDIA, 'Wikipedia'),
        (PLACENAME, 'PlaceName'),
    )

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

    username = models.CharField(
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
        choices=QUERY_TYPES,
    )

    layer_name = models.CharField(
        help_text=_(
            'Required name of the actual layer/feature to retrieve (Property name.'),
        blank=False,
        null=False,
        max_length=200,
    )

    layer_namespace = models.CharField(
        help_text=_('Optional namespace containing the typename to query (WMS/WFS).'),
        blank=True,
        null=True,
        max_length=200,
    )

    layer_typename = models.CharField(
        help_text=_('Optional layer type name to get from the service (WMS/WFS).'),
        blank=True,
        null=True,
        max_length=200,
    )

    layer_workspace = models.CharField(
        help_text=_('Optional workspace containing the typename to query (WMS/WFS).'),
        blank=True,
        null=True,
        max_length=200,
    )

    cache_duration = models.IntegerField(
        help_text=_('Service refresh time in seconds - determines Cache persistence'),
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

    tolerance = models.FloatField(
        help_text=_(
            'Tolerance around query point in meters. Used for bounding box queries.'
            'Also determines cache hit range for all values'),
        blank=True,
        null=True,
        default=10
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

    test_x = models.FloatField(
        help_text=_('Longitude of known value to test service.'),
        blank=True,
        null=True,
    )

    test_y = models.FloatField(
        help_text=_('Latitude of known value to test service.'),
        blank=True,
        null=True,
    )

    test_value = models.CharField(
        help_text=_('Known value expected at test coordinates.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    status = models.BooleanField(
        help_text=_('Status of this service (determined by test coordinate & value'),
        blank=True,
        null=True,
    )

    permission_groups = models.ManyToManyField(
        AuthGroup,
        help_text=_('List of auth groups with access to this service.'),
        blank=True,
    )

    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.name
