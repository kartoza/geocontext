from django.db import models
from django.conf import settings


class UserProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_profile'
    )

    user_tier = models.ForeignKey(
        'geocontext.UserTier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    subscribed = models.BooleanField(
        default=False
    )
