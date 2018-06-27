# coding=utf-8
"""Model for ContextGroup"""

from django.db import models
from django.utils.translation import ugettext_lazy as _


class ContextGroup(models.Model):
    """Context Group"""

    key = models.CharField(
        help_text=_('Key of context group.'),
        blank=False,
        null=False,
        max_length=200,
        unique=True,
    )

    name = models.CharField(
        help_text=_('Display Name of Context Service.'),
        blank=False,
        null=False,
        max_length=200,
    )

    def __str__(self):
        return self.name
