from django.db import models

from geocontext.models.group import Group
from geocontext.models.service import Service


class GroupServices(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, default=None)
    order = models.PositiveIntegerField(
        verbose_name='Order',
        null=False,
        blank=True,
        default=0
    )

    class Meta:
        unique_together = ('group', 'service',)
