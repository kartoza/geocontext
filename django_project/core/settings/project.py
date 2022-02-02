"""Project level settings.

Adjust these values as needed but don't commit passwords etc. to any public
repository!
"""

import ast
import os  # noqa
from django.utils.translation import ugettext_lazy as _
from .contrib import *  # noqa

# Project apps
INSTALLED_APPS += (
    'base',
    'geocontext',
)

# Set debug to false for production
DEBUG = TEMPLATE_DEBUG = False

# Set languages which want to be translated
LANGUAGES = (
    ('en', _('English')),
)

VALID_DOMAIN = [
    '0.0.0.0',
]

ENABLE_API_TOKEN = ast.literal_eval(
    os.environ.get('ENABLE_API_TOKEN', 'False')
)
