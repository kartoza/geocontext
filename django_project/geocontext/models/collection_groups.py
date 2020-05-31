from django.db import models

from geocontext.models.collection import Collection
from geocontext.models.group import Group


class CollectionGroups(models.Model):
    """Collection Groups"""
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, default=None)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    order = models.PositiveIntegerField(
        verbose_name='Order',
        null=False,
        blank=True,
        default=0
    )

    class Meta:
        unique_together = ('collection', 'group',)
