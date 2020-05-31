from django.db import models

from geocontext.models.group import Group
from geocontext.models.csr import CSR


class GroupServices(models.Model):
    """Context Group Services"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    csr = models.ForeignKey(CSR, on_delete=models.CASCADE, default=None)
    order = models.PositiveIntegerField(
        verbose_name='Order',
        null=False,
        blank=True,
        default=0
    )

    class Meta:
        unique_together = ('group', 'csr',)
