# coding=utf-8
"""Model for ContextGroupServices"""

from django.db import models

from geocontext.models.context_group import ContextGroup
from geocontext.models.context_service_registry import ContextServiceRegistry



class ContextGroupServices(models.Model):
    """Context Group Services"""

    context_group = models.ForeignKey(ContextGroup, on_delete=models.CASCADE)
    context_service_registry = models.ForeignKey(
        ContextServiceRegistry, on_delete=models.CASCADE)
    order = models.IntegerField(
        verbose_name='Order',
        null=False,
        blank=True
    )
