import os
import unittest
from unittest.mock import patch

from django.test import TestCase

from geocontext.models.cache import Cache
from geocontext.tests.models.model_factories import CSRF
from geocontext.utilities import ServiceDefinitions
from geocontext.models.utilities import (
    CSRUtils,
    retrieve_external_csr,
    UtilArg
)

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '../data')


@patch.object(CSRUtils, 'get_csr')
class TestCRSUtils(TestCase):
    """Test CSR models."""

    def test_retrieve_value1(self, mock_get_csr):
        """Test retrieving value from a point with same CRS."""
        x = 18.42
        y = -29.71

        csr = CSRF.create()
        csr.url = 'https://maps.kartoza.com/geoserver/wfs'
        csr.query_type = ServiceDefinitions.WFS
        csr.layer_typename = 'kartoza:water_management_areas'
        csr.service_version = '1.0.0'
        csr.result_regex = 'gml:name'
        csr.save()
        mock_get_csr.return_value = csr

        csr_util = CSRUtils(csr.key, x, y, csr.srid)
        util_arg = UtilArg(group_key=csr.key, csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_cache()

        expected_value = '14 - Lower Orange'
        self.assertEqual(result.value, expected_value)
        self.assertIsNotNone(result.geometry)
        self.assertEqual(result.geometry.geom_type, 'Polygon')
        self.assertTrue(result.geometry.valid)

        caches = Cache.objects.filter(csr=csr)
        self.assertIsNotNone(caches)
        cache = caches[0]
        self.assertEqual(cache.value, expected_value)
        self.assertEqual(cache.geometry.geom_type, 'Polygon')
        self.assertEqual(cache.geometry.srid, 4326)

    @unittest.skip("Please fix this")
    def test_retrieve_value2(self, mock_get_csr):
        """Test retrieving value from a point with different CRS."""
        x = 18.42
        y = -29.71

        csr = CSRF.create()
        csr.url = 'http://maps.kartoza.com/geoserver/wfs'
        csr.query_type = ServiceDefinitions.WFS
        csr.layer_typename = 'sa_provinces'
        csr.service_version = '1.0.0'
        csr.srid = 3857
        csr.result_regex = 'kartoza:sa_provinces'
        csr.save()
        mock_get_csr.return_value = csr

        csr_util = CSRUtils(csr.key, x, y, srid=4326)
        util_arg = UtilArg(group_key=csr.key, csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_cache()

        expected_value = 'Northern Cape'
        self.assertEqual(result.value, expected_value)
        self.assertIsNotNone(result.value)
        self.assertEqual(result.geometry.geom_type, 'MultiPolygon')
        self.assertTrue(result.geometry.valid)

        caches = Cache.objects.filter(csr=csr)
        self.assertIsNotNone(caches)
        cache = caches[0]
        self.assertEqual(cache.value, expected_value)
        self.assertEqual(cache.geometry.geom_type, 'MultiPolygon')
        # Automatically projected to 4326
        self.assertEqual(cache.geometry.srid, 4326)

    @unittest.skip("Please fix this")
    def test_retrieve_value_geoserver(self, mock_get_csr):
        """Test retrieving value from a geoserver service."""
        x = 18.42
        y = -29.71

        csr = CSRF.create()
        csr.url = 'http://maps.kartoza.com/geoserver/wfs'
        csr.query_type = ServiceDefinitions.WFS
        csr.layer_typename = 'sa_provinces'
        csr.service_version = '1.0.0'
        csr.result_regex = 'kartoza:sa_provinces'
        csr.save()
        mock_get_csr.return_value = csr

        csr_util = CSRUtils(csr.key, x, y, csr.srid)
        util_arg = UtilArg(group_key=csr.key, csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_cache()

        expected_value = 'Northern Cape'
        self.assertEqual(result.value, expected_value)
        self.assertIsNotNone(result.value)
        self.assertEqual(result.geometry.geom_type, 'MultiPolygon')
        self.assertTrue(result.geometry.valid)

        caches = Cache.objects.filter(csr=csr)
        self.assertIsNotNone(caches)
        cache = caches[0]
        self.assertEqual(cache.value, expected_value)
        self.assertEqual(cache.geometry.geom_type, 'MultiPolygon')
        # Automatically projected to 4326
        self.assertEqual(cache.geometry.srid, 4326)

    def test_retrieve_value_wms(self, mock_get_csr):
        """Test retrieving value from a point with WMS source."""
        x = 27.8
        y = -32.1

        csr = CSRF.create()
        csr.url = 'https://maps.kartoza.com/geoserver/wms'
        csr.query_type = ServiceDefinitions.WMS
        csr.layer_typename = 'kartoza:south_africa'
        csr.service_version = '1.3.0'
        csr.result_regex = 'kartoza:GRAY_INDEX'
        csr.save()
        mock_get_csr.return_value = csr

        csr_util = CSRUtils(csr.key, x, y, csr.srid)

        util_arg = UtilArg(group_key=csr.key, csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_cache()

        expected_value = '746.0'
        self.assertEqual(result.value, expected_value)
        self.assertIsNotNone(result.value)

        caches = Cache.objects.filter(csr=csr)
        self.assertIsNotNone(caches)
        cache = caches[0]
        self.assertEqual(cache.value, expected_value)

    def test_retrieve_value_arcrest(self, mock_get_csr):
        """Test retrieving value from a point with ArcRest source.
        """
        x = 19.14
        y = -32.32

        csr = CSRF.create()
        csr.url = (
            'https://portal.environment.gov.za/server/rest/services/Corp/'
            'ProtectedAreas/MapServer/')
        csr.srid = 4326
        csr.query_type = ServiceDefinitions.ARCREST
        csr.layer_typename = 'all:10'
        csr.service_version = 'ArcRest 1.0.0'
        csr.result_regex = 'value'
        csr.save()
        mock_get_csr.return_value = csr

        csr_util = CSRUtils(csr.key, x, y, csr.srid)
        util_arg = UtilArg(group_key=csr.key, csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_cache()

        expected_value = (
            'Cape Floral Region Protected Areas: Cederberg Wilderness Area')
        self.assertEqual(result.value, expected_value)
        self.assertIsNotNone(result.value)

        caches = Cache.objects.filter(csr=csr)
        self.assertIsNotNone(caches)
        cache = caches[0]
        self.assertEqual(cache.value, expected_value)

    def test_retrieve_value_placename(self, mock_get_csr):
        """Test retrieving value from a point with ArcRest source.
        """
        x = 19.14
        y = -32.32

        csr = CSRF.create()
        csr.url = (
            'http://api.geonames.org/findNearbyPlaceNameJSON')
        csr.srid = 4326
        csr.query_type = ServiceDefinitions.PLACENAME
        csr.layer_typename = 'Find Nearby Place Name'
        csr.service_version = 'Version 1.0.0'
        csr.result_regex = 'toponymName'
        csr.api_key = 'christiaanvdm'
        csr.save()
        mock_get_csr.return_value = csr

        csr_util = CSRUtils(csr.key, x, y, csr.srid)
        util_arg = UtilArg(group_key=csr.key, csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)
        self.assertIsNotNone(new_util_arg)
        result = new_util_arg.csr_util.create_cache()

        expected_value = 'Wuppertal'
        self.assertEqual(result.value, expected_value)
        self.assertIsNotNone(result.value)

        caches = Cache.objects.filter(csr=csr)
        self.assertIsNotNone(caches)
        cache = caches[0]
        self.assertEqual(cache.value, expected_value)

    @unittest.skip("Please fix this")
    def test_retrieve_value_invalid(self, mock_get_csr):
        """Test retrieving value from a point with different CRS.

        The CRS is 4326 (query), 3857 (service)
        """
        x = 0
        y = 0

        csr = CSRF.create()
        csr.url = 'https://maps.kartoza.com/geoserver/wfs'
        csr.query_type = ServiceDefinitions.WFS
        csr.layer_typename = 'kartoza:sa_provinces'
        csr.service_version = '1.0.0'
        csr.result_regex = 'gml:name'
        csr.srid = 3857
        csr.save()
        mock_get_csr.return_value = csr

        csr_util = CSRUtils(csr.key, x, y, csr.srid)
        util_arg = UtilArg(group_key=csr.key, csr_util=csr_util)
        new_util_arg = retrieve_external_csr(util_arg)

        self.assertIsNone(new_util_arg)

    def test_parse_request_value(self, mock_get_csr):
        """Test parse value for WMS response."""
        csr = CSRF.create()
        csr.url = 'https://maps.kartoza.com/geoserver/wms'
        csr.srid = 3857
        csr.query_type = ServiceDefinitions.WMS
        csr.layer_typename = 'kartoza:south_africa'
        csr.service_version = '1.1.1'
        csr.result_regex = 'kartoza:GRAY_INDEX'
        csr.save()
        mock_get_csr.return_value = csr

        wms_response_file = os.path.join(test_data_directory, 'wms.xml')
        with open(wms_response_file) as f:
            response = f.read()

        csr_util = CSRUtils(csr.key, 0, 0, csr.srid)
        value = csr_util.parse_request_value(response)

        self.assertIsNotNone(value)
        self.assertEqual('746.0', value)
