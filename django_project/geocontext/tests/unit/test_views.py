from datetime import datetime
import os

from django.test import TestCase

from base.management.commands.utilities import import_data
from geocontext.models.services import Service
from geocontext.models.utilities import ServiceUtils, retrieve_cache

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')

