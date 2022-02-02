from django.contrib.auth.models import Group as AuthGroup
from django.db import models
from django.utils.translation import ugettext_lazy as _

from geocontext.models.validators import key_validator
from geocontext.models.group import Group


class Collection(models.Model):
    """Collection"""
    key = models.CharField(
        help_text=_('Key of collection.'),
        blank=False,
        null=False,
        max_length=200,
        unique=True,
        validators=[key_validator]
    )
    name = models.CharField(
        help_text=_('Display Name of Collection.'),
        blank=False,
        null=False,
        max_length=200,
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text='Description of the Collection.'
    )
    groups = models.ManyToManyField(
        Group,
        help_text=_('List of group in this collection.'),
        through='CollectionGroups',
        blank=True,
    )
    permission_groups = models.ManyToManyField(
        AuthGroup,
        help_text=_('List of auth groups with access to this collection.'),
        blank=True,
    )

    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.name

    def get_ordered_groups(self):
        """Helper to retrieve groups in order."""
        return self.collectiongroups_set.all().order_by('order')
