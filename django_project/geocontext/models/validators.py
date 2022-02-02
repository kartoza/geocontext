from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


key_validator = RegexValidator(
    regex=r'^[0-9a-z_]+$',
    message=_('Key must only contains lower case or underscore.'),
    code='invalid_key'
)
