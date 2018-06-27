# coding=utf-8
"""Test for context service registry model."""

from django.test import TestCase

from geocontext.models.context_service_registry import ContextServiceRegistry
from geocontext.models.context_cache import ContextCache
from geocontext.tests.models.model_factories import ContextServiceRegistryF


class TestContextServiceRegistry(TestCase):
    """Test CSR models."""

    def test_ContextServiceRegistry_create(self):
        """Test CSR model creation."""

        model = ContextServiceRegistryF.create()

        # check if PK exists.
        self.assertTrue(model.pk is not None)

        # check if model key exists.
        self.assertTrue(model.key is not None)

    def test_retrieve_context_value1(self):
        """Test retrieving context value from a point with same CRS.

        The CRS is 4326 (query, service)
        """
        x = 27.8
        y = -32.1

        service_registry = ContextServiceRegistryF.create()
        service_registry.url = (
            'http://maps.kartoza.com/web/?map=/web/kartoza/kartoza.qgs')
        service_registry.srid = 4326
        service_registry.query_type = ContextServiceRegistry.WFS
        service_registry.layer_typename = 'water_management_area'
        service_registry.service_version = '1.0.0'

        service_registry.result_regex = 'qgs:name'

        service_registry.save()

        result = service_registry.retrieve_context_value(x, y)
        expected_value = '12 - Mzimvubu to Keiskamma'
        self.assertEqual(result.value, expected_value)
        self.assertIsNotNone(result.geometry)
        self.assertEqual(result.geometry.geom_type, 'Polygon')
        self.assertTrue(result.geometry.valid)

        context_caches = ContextCache.objects.filter(
            service_registry=service_registry)
        self.assertIsNotNone(context_caches)
        context_cache = context_caches[0]
        self.assertEqual(context_cache.value, expected_value)
        self.assertEqual(context_cache.geometry.geom_type, 'Polygon')
        self.assertEqual(context_cache.geometry.srid, 4326)

    def test_retrieve_context_value2(self):
        """Test retrieving context value from a point with different CRS.

        The CRS is 4326 (query), 3857 (service)
        """
        x = 27.8
        y = -32.1

        service_registry = ContextServiceRegistryF.create()
        service_registry.url = (
            'http://maps.kartoza.com/web/?map=/web/kartoza/kartoza.qgs')
        service_registry.srid = 3857
        service_registry.query_type = ContextServiceRegistry.WFS
        service_registry.layer_typename = 'sa_provinces'
        service_registry.service_version = '1.0.0'

        service_registry.result_regex = 'qgs:provname'

        service_registry.save()

        result = service_registry.retrieve_context_value(x, y)
        expected_value = 'Eastern Cape'
        self.assertEqual(result.value, expected_value)
        self.assertIsNotNone(result.value)
        self.assertEqual(result.geometry.geom_type, 'MultiPolygon')
        self.assertTrue(result.geometry.valid)

        context_caches = ContextCache.objects.filter(
            service_registry=service_registry)
        self.assertIsNotNone(context_caches)
        context_cache = context_caches[0]
        self.assertEqual(context_cache.value, expected_value)
        self.assertEqual(context_cache.geometry.geom_type, 'MultiPolygon')
        # Automatically projected to 4326
        self.assertEqual(context_cache.geometry.srid, 4326)

    def test_retrieve_context_value_invalid(self):
        """Test retrieving context value from a point with different CRS.

        The CRS is 4326 (query), 3857 (service)
        """
        x = 0
        y = 0

        service_registry = ContextServiceRegistryF.create()
        service_registry.url = (
            'http://maps.kartoza.com/web/?map=/web/kartoza/kartoza.qgs')
        service_registry.srid = 3857
        service_registry.query_type = ContextServiceRegistry.WFS
        service_registry.layer_typename = 'sa_provinces'
        service_registry.service_version = '1.0.0'

        service_registry.result_regex = 'qgs:provname'

        service_registry.save()

        result = service_registry.retrieve_context_value(x, y)
        self.assertIsNone(result)
