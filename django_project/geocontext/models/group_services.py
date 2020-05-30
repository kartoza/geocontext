from django.db import models

from geocontext.models.group import ContextGroup
from geocontext.models.service_registry import ContextServiceRegistry



class ContextGroupServices(models.Model):
    """Context Group Services"""

    class Meta:
        unique_together = ('context_group', 'context_service_registry',)

    context_group = models.ForeignKey(ContextGroup, on_delete=models.CASCADE)
    context_service_registry = models.ForeignKey(
        ContextServiceRegistry, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(
        verbose_name='Order',
        null=False,
        blank=True,
        default=0
    )
