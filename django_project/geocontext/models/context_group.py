from django.db import models
from django.utils.translation import ugettext_lazy as _
from geocontext.models.validators import key_validator

from geocontext.models.context_service_registry import ContextServiceRegistry


class ContextGroup(models.Model):
    """Context Group"""

    GROUP_TYPE_TEXT = 'text'
    GROUP_TYPE_GRAPH = 'graph'

    GROUP_TYPE_CHOICES = (
        (GROUP_TYPE_TEXT, 'Text'),
        (GROUP_TYPE_GRAPH, 'Graph')  # The values can be used for graph
    )

    key = models.CharField(
        help_text=_('Key of context group.'),
        blank=False,
        null=False,
        max_length=200,
        unique=True,
        validators=[key_validator],
    )

    name = models.CharField(
        help_text=_('Display Name of Context Service.'),
        blank=False,
        null=False,
        max_length=200,
    )

    description = models.TextField(
        null=True,
        blank=True,
        help_text='Description of the Context Group.'
    )

    context_service_registries = models.ManyToManyField(
        ContextServiceRegistry,
        help_text=_('List of context service registry in the context group.'),
        through='ContextGroupServices',
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
            'Indicates if this registry returns data from which a graph can '
            'be drawn.'),
        blank=True,
        null=False,
        default=False,
    )

    def __str__(self):
        return self.name

    def get_ordered_context_service_registries(self):
        """Helper to retrieve CSR in order."""
        return self.contextgroupservices_set.all().order_by('order')
