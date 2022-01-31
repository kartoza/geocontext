from django.utils.translation import gettext_lazy as _
from django.conf import settings

from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions


class CustomTokenAuthentication(TokenAuthentication):
    """
    Customized token based authentication.

    Clients should authenticate by passing the token key in the url.
    For example:

        &token=401f7ac837da42b97f613d789819ff93537bee6a
    """

    def authenticate(self, request):
        token = request.GET.get('token', '')
        if not settings.ENABLE_API_TOKEN:
            return None, None

        if not token:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)
