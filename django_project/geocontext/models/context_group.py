# coding=utf-8
"""Model for ContextGroup"""

from django.db import models
from django.utils.translation import ugettext_lazy as _
from geocontext.models.validators import key_validator

from geocontext.models.context_service_registry import ContextServiceRegistry


class ContextGroup(models.Model):
    """Context Group"""

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

    def __str__(self):
        return self.name
