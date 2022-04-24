from django.db import models

from geocontext.models import UserTier


class OfferTier(models.Model):
    """ Offer Tier """

    description = models.TextField(
        default='',
        blank=True
    )
    quantity = models.IntegerField(
        default=0,
        verbose_name='The quantity of the offer'
    )
    user_tier = models.ForeignKey(UserTier, on_delete=models.CASCADE, default=None)
