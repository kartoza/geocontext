# coding=utf-8
"""Model for CollectionGroups"""

from django.db import models

from geocontext.models.context_collection import ContextCollection
from geocontext.models.context_group import ContextGroup


class CollectionGroups(models.Model):
    """Collection Groups"""

    context_group = models.ForeignKey(ContextGroup, on_delete=models.CASCADE)
    context_collection = models.ForeignKey(
        ContextCollection, on_delete=models.CASCADE)
    order = models.IntegerField(
        verbose_name='Order',
        null=False,
        blank=True,
        default=0
    )
