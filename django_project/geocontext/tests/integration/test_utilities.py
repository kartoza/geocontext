import os
import unittest
from datetime import datetime
from unittest.mock import patch

from django.test import TestCase

from base.management.commands.utilities import import_data
from geocontext.models.cache import Cache
from geocontext.models.service import Service
from geocontext.models.utilities import (
    create_cache,
    retrieve_cache,
    ServiceUtils,
    retrieve_external_service,
    UtilArg
)
from geocontext.tests.models.model_factories import ServiceF
from geocontext.utilities import ServiceDefinitions


test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '../data')


