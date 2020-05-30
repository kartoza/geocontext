from django.db import models

from geocontext.models.group import ContextGroup
from geocontext.models.csr import CSR


class ContextGroupServices(models.Model):
    """Context Group Services"""

    group = models.ForeignKey(ContextGroup, on_delete=models.CASCADE)
    csr = models.ForeignKey(CSR, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(
        verbose_name='Order',
        null=False,
        blank=True,
        default=0
    )

    class Meta:
        unique_together = ('group', 'csr',)
