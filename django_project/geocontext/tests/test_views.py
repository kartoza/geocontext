# coding=utf-8
"""Test views."""

from datetime import datetime

from django.test import TestCase
from django.core import management

from geocontext.models.context_service_registry import ContextServiceRegistry

from geocontext.models.utilities import retrieve_context


class TestGeoContextView(TestCase):
    """Test for geocontext view."""

    def setUp(self):
        """Setup test data."""
        management.call_command('import_data')
        pass

    def tearDown(self):
        """Delete all service registry data."""
        service_registries = ContextServiceRegistry.objects.all()
        for service_registry in service_registries:
            service_registry.delete()

    def test_cache_retrieval(self):
        """Test for retrieving from service registry and cache."""
        x = 27.8
        y = -32.1

        service_registry = ContextServiceRegistry.objects.get(
            key='water_management_area')

        start_direct = datetime.now()
        retrieve_context(x, y, service_registry.key)
        end_direct = datetime.now()

        start_cache = datetime.now()
        retrieve_context(x, y, service_registry.key)
        end_cache = datetime.now()

        duration_direct = end_direct - start_direct
        duration_cache = end_cache - start_cache
        message = 'Direct: %.5f. Cache: %.5f' % (
            duration_direct.total_seconds(), duration_cache.total_seconds())
        print(message)
        self.assertGreater(duration_direct, duration_cache, message)
