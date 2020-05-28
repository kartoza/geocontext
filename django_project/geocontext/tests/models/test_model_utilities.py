import os
import unittest
from unittest.mock import patch

from django.test import TestCase

from geocontext.models.context_cache import ContextCache
from geocontext.tests.models.model_factories import ContextServiceRegistryF
from geocontext.utilities import ServiceDefinitions
from geocontext.models.utilities import (
    CSRUtils,
    retrieve_external_csr,
    UtilArg
)

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '../data')


@patch.object(CSRUtils, 'get_service_registry')
class TestCRSUtils(TestCase):
    """Test CSR models."""

    def test_retrieve_context_value1(self, mock_get_service_registry):
        """Test retrieving context value from a point with same CRS."""
        x = 18.42
        y = -29.71

        service_registry = ContextServiceRegistryF.create()
        service_registry.url = 'https://maps.kartoza.com/geoserver/wfs'
        service_registry.query_type = ServiceDefinitions.WFS
        service_registry.layer_typename = 'kartoza:water_management_areas'
        service_registry.service_version = '1.0.0'
        service_registry.result_regex = 'gml:name'
        service_registry.save()
        mock_get_service_registry.return_value = service_registry

        csr_util = CSRUtils(service_registry.key, x, y, service_registry.srid)
        util_arg = UtilArg(group_key=service_registry.key,
                           csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_context_cache()

        expected_value = '14 - Lower Orange'
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

    @unittest.skip("Please fix this")
    def test_retrieve_context_value2(self, mock_get_service_registry):
        """Test retrieving context value from a point with different CRS."""
        x = 18.42
        y = -29.71

        service_registry = ContextServiceRegistryF.create()
        service_registry.url = 'http://maps.kartoza.com/geoserver/wfs'
        service_registry.query_type = ServiceDefinitions.WFS
        service_registry.layer_typename = 'sa_provinces'
        service_registry.service_version = '1.0.0'
        service_registry.srid = 3857
        service_registry.result_regex = 'kartoza:sa_provinces'
        service_registry.save()
        mock_get_service_registry.return_value = service_registry

        csr_util = CSRUtils(service_registry.key, x, y, srid=4326)
        util_arg = UtilArg(group_key=service_registry.key,
                           csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_context_cache()

        expected_value = 'Northern Cape'
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

    @unittest.skip("Please fix this")
    def test_retrieve_context_value_geoserver(self, mock_get_service_registry):
        """Test retrieving context value from a geoserver service."""
        x = 18.42
        y = -29.71

        service_registry = ContextServiceRegistryF.create()
        service_registry.url = 'http://maps.kartoza.com/geoserver/wfs'
        service_registry.query_type = ServiceDefinitions.WFS
        service_registry.layer_typename = 'sa_provinces'
        service_registry.service_version = '1.0.0'
        service_registry.result_regex = 'kartoza:sa_provinces'
        service_registry.save()
        mock_get_service_registry.return_value = service_registry

        csr_util = CSRUtils(service_registry.key, x, y, service_registry.srid)
        util_arg = UtilArg(group_key=service_registry.key,
                           csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_context_cache()

        expected_value = 'Northern Cape'
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

    def test_retrieve_context_value_wms(self, mock_get_service_registry):
        """Test retrieving context value from a point with WMS source."""
        x = 27.8
        y = -32.1

        service_registry = ContextServiceRegistryF.create()
        service_registry.url = 'https://maps.kartoza.com/geoserver/wms'
        service_registry.query_type = ServiceDefinitions.WMS
        service_registry.layer_typename = 'kartoza:south_africa'
        service_registry.service_version = '1.3.0'
        service_registry.result_regex = 'kartoza:GRAY_INDEX'
        service_registry.save()
        mock_get_service_registry.return_value = service_registry

        csr_util = CSRUtils(service_registry.key, x, y, service_registry.srid)

        util_arg = UtilArg(group_key=service_registry.key,
                           csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_context_cache()

        expected_value = '746.0'
        self.assertEqual(result.value, expected_value)
        self.assertIsNotNone(result.value)

        context_caches = ContextCache.objects.filter(
            service_registry=service_registry)
        self.assertIsNotNone(context_caches)
        context_cache = context_caches[0]
        self.assertEqual(context_cache.value, expected_value)

    def test_retrieve_context_value_arcrest(self, mock_get_service_registry):
        """Test retrieving context value from a point with ArcRest source.
        """
        x = 19.14
        y = -32.32

        service_registry = ContextServiceRegistryF.create()
        service_registry.url = (
            'https://portal.environment.gov.za/server/rest/services/Corp/'
            'ProtectedAreas/MapServer/')
        service_registry.srid = 4326
        service_registry.query_type = ServiceDefinitions.ARCREST
        service_registry.layer_typename = 'all:10'
        service_registry.service_version = 'ArcRest 1.0.0'
        service_registry.result_regex = 'value'
        service_registry.save()
        mock_get_service_registry.return_value = service_registry

        csr_util = CSRUtils(service_registry.key, x, y, service_registry.srid)
        util_arg = UtilArg(group_key=service_registry.key,
                           csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_context_cache()

        expected_value = (
            'Cape Floral Region Protected Areas: Cederberg Wilderness Area')
        self.assertEqual(result.value, expected_value)
        self.assertIsNotNone(result.value)

        context_caches = ContextCache.objects.filter(
            service_registry=service_registry)
        self.assertIsNotNone(context_caches)
        context_cache = context_caches[0]
        self.assertEqual(context_cache.value, expected_value)

    def test_retrieve_context_value_placename(self, mock_get_service_registry):
        """Test retrieving context value from a point with ArcRest source.
        """
        x = 19.14
        y = -32.32

        service_registry = ContextServiceRegistryF.create()
        service_registry.url = (
            'http://api.geonames.org/findNearbyPlaceNameJSON')
        service_registry.srid = 4326
        service_registry.query_type = ServiceDefinitions.PLACENAME
        service_registry.layer_typename = 'Find Nearby Place Name'
        service_registry.service_version = 'Version 1.0.0'
        service_registry.result_regex = 'toponymName'
        service_registry.api_key = 'christiaanvdm'
        service_registry.save()
        mock_get_service_registry.return_value = service_registry

        csr_util = CSRUtils(service_registry.key, x, y, service_registry.srid)
        util_arg = UtilArg(group_key=service_registry.key,
                           csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_context_cache()

        expected_value = 'Wuppertal'
        self.assertEqual(result.value, expected_value)
        self.assertIsNotNone(result.value)

        context_caches = ContextCache.objects.filter(
            service_registry=service_registry)
        self.assertIsNotNone(context_caches)
        context_cache = context_caches[0]
        self.assertEqual(context_cache.value, expected_value)

    @unittest.skip("Please fix this")
    def test_retrieve_context_value_invalid(self, mock_get_service_registry):
        """Test retrieving context value from a point with different CRS.

        The CRS is 4326 (query), 3857 (service)
        """
        x = 0
        y = 0

        service_registry = ContextServiceRegistryF.create()
        service_registry.url = 'https://maps.kartoza.com/geoserver/wfs'
        service_registry.query_type = ServiceDefinitions.WFS
        service_registry.layer_typename = 'kartoza:sa_provinces'
        service_registry.service_version = '1.0.0'
        service_registry.result_regex = 'gml:name'
        service_registry.srid = 3857
        service_registry.save()
        mock_get_service_registry.return_value = service_registry

        csr_util = CSRUtils(service_registry.key, x, y, service_registry.srid)
        util_arg = UtilArg(group_key=service_registry.key,
                           csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)

        self.assertIsNone(new_util_arg)

    def test_parse_request_value(self, mock_get_service_registry):
        """Test parse value for WMS response."""
        service_registry = ContextServiceRegistryF.create()
        service_registry.url = 'https://maps.kartoza.com/geoserver/wms'
        service_registry.srid = 3857
        service_registry.query_type = ServiceDefinitions.WMS
        service_registry.layer_typename = 'kartoza:south_africa'
        service_registry.service_version = '1.1.1'
        service_registry.result_regex = 'kartoza:GRAY_INDEX'
        service_registry.save()
        mock_get_service_registry.return_value = service_registry

        wms_response_file = os.path.join(test_data_directory, 'wms.xml')
        with open(wms_response_file) as f:
            response = f.read()

        csr_util = CSRUtils(service_registry.key, 0, 0, service_registry.srid)
        value = csr_util.parse_request_value(response)

        self.assertIsNotNone(value)
        self.assertEqual('746.0', value)
