from django.db import models
from django.utils.translation import ugettext_lazy as _
from geocontext.models.validators import key_validator

from geocontext.models.context_group import ContextGroup


class ContextCollection(models.Model):
    """Context Collection"""

    key = models.CharField(
        help_text=_('Key of context collection.'),
        blank=False,
        null=False,
        max_length=200,
        unique=True,
        validators=[key_validator]
    )

    name = models.CharField(
        help_text=_('Display Name of Context Collection.'),
        blank=False,
        null=False,
        max_length=200,
    )


    description = models.TextField(
        null=True,
        blank=True,
        help_text='Description of the Context Collection.'
    )

    context_groups = models.ManyToManyField(
        ContextGroup,
        help_text=_('List of context group in this context collection.'),
        through='CollectionGroups',
        blank=True,
    )

    def __str__(self):
        return self.name

    def get_ordered_context_groups(self):
        """Helper to retrieve context groups in order."""
        return self.collectiongroups_set.all().order_by('order')
