
"""Configuration for production server"""
# noinspection PyUnresolvedReferences
from .prod import *  # noqa
import os

DEBUG = False

ALLOWED_HOSTS = ['*']

ADMINS = (
    ('Dimas Ciputra', 'dimas@kartoza.com'),
    ('Andre Theron', 'andre.theron@kartoza.com '),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DATABASE_NAME'),
        'USER': os.environ.get('DATABASE_USERNAME'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
        'HOST': os.environ.get('DATABASE_HOST'),
        'PORT': 5432,
        'TEST_NAME': 'unittests',
    }
}