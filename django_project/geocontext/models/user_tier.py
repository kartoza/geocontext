from django.db import models


class UserTier(models.Model):

    name = models.CharField(
        max_length=256,
        null=False,
        blank=False
    )

    order = models.IntegerField(
        default=0,
        verbose_name='Order on website'
    )

    description = models.TextField(
        default='',
        blank=True
    )

    request_limit = models.CharField(
        default='100/day',
        max_length=100,
        help_text='API request limit for user. '
                  'Enter "-" for unlimited requests',
        null=False,
        blank=False
    )

    price_amount = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        default=0
    )

    logo = models.FileField(
        null=True,
        blank=True,
        upload_to='user_tier_logo/'
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', )
