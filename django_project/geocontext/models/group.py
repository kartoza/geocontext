from django.db import models
from django.utils.translation import ugettext_lazy as _

from geocontext.models.service import Service
from geocontext.models.validators import key_validator


class Group(models.Model):
    GROUP_TYPE_TEXT = 'text'
    GROUP_TYPE_GRAPH = 'graph'

    GROUP_TYPE_CHOICES = (
        (GROUP_TYPE_TEXT, 'Text'),
        (GROUP_TYPE_GRAPH, 'Graph')
    )

    key = models.CharField(
        help_text=_('Key of group.'),
        blank=False,
        null=False,
        max_length=200,
        unique=True,
        validators=[key_validator],
    )

    name = models.CharField(
        help_text=_('Display Name of Service.'),
        blank=False,
        null=False,
        max_length=200,
    )

    description = models.TextField(
        null=True,
        blank=True,
        help_text='Description of the Group.'
    )

    services = models.ManyToManyField(
        Service,
        help_text=_('List of services in the group.'),
        through='GroupServices',
        blank=True,
    )

    group_type = models.CharField(
        help_text='Type of the group to determine the UI.',
        null=False,
        blank=False,
        default=GROUP_TYPE_TEXT,
        choices=GROUP_TYPE_CHOICES,
        max_length=10
    )

    graphable = models.BooleanField(
        help_text=_(
            'Indicates if this service returns data from which a graph can be drawn.'),
        blank=True,
        null=False,
        default=False,
    )

    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.name

    def get_ordered_service_list(self):
        """Helper to retrieve services in order."""
        return self.groupservices_set.all().order_by('order')
