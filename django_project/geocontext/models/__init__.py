from geocontext.models.cache import *
from geocontext.models.service import *
from geocontext.models.group_services import *
from geocontext.models.collection_groups import *
from geocontext.models.group import *
from geocontext.models.collection import *

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
