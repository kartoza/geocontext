import os

from unittest.mock import patch

from django.test import TestCase

from geocontext.models.utilities import CSRUtils

from django.contrib.gis.geos import Point
from django.test import SimpleTestCase
from geocontext.utilities import (
    convert_coordinate,
    dms_dd,
    get_bbox,
    parse_dms,
)

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')


class TestUtilities(SimpleTestCase):
    """Test for utilities module."""

    def test_convert_coordinate(self):
        """Test convert_coordinate method."""
        result = convert_coordinate(Point(1, 1, srid=4326), 3857)
        self.assertAlmostEqual(result[0], 111319.49, places=2)
        self.assertAlmostEqual(result[1], 111325.14, places=2)

    def test_get_bbox(self):
        """Test get_bbox function."""
        bbox = get_bbox(Point(1, 10), 0.0001, string=False)
        self.assertEqual('0.9999, 9.9999, 1.0001, 10.0001', bbox)
        self.assertLess(bbox[0], bbox[2])
        self.assertLess(bbox[1], bbox[3])

        bbox = get_bbox(Point(1, 10), 0.0001, string=False)
        self.assertLess(bbox[0], bbox[2])
        self.assertLess(bbox[1], bbox[3])

    def test_dms_dd_south(self):
        """Test dms to dd function with negative."""
        decimal = dms_dd(-32, 7, 23.2)
        self.assertEqual(-32.1231, round(decimal, 4))

    def test_dms_east(self):
        """Test dms to dd function."""
        decimal = dms_dd(27, 49, 23.2)
        self.assertEqual(27.823100, round(decimal, 4))

    def test_parse_dms_south(self):
        """Test dms to dd function."""
        degrees, minutes, seconds = parse_dms("32:07:23.2:S")
        self.assertEqual(-32, degrees)
        self.assertEqual(7, minutes)
        self.assertEqual(23.2, seconds)

    def test_parse_dms_east(self):
        """Test dms to dd function."""
        degrees, minutes, seconds = parse_dms("27:49:23.2:E")
        self.assertEqual(27, degrees)
        self.assertEqual(49, minutes)
        self.assertEqual(23.2, seconds)

    def test_parse_dms_invalid(self):
        """Test dms to dd function on invalid string."""
        self.assertRaises(ValueError, parse_dms, "27:49:23.2E")
        self.assertRaises(ValueError, parse_dms, "E:49:23.2E")
        self.assertRaises(ValueError, parse_dms, "274923.2E")
        self.assertRaises(ValueError, parse_dms, "27:49:23.2:")
        self.assertRaises(ValueError, parse_dms, "27:49:23.2:east")
        self.assertRaises(ValueError, parse_dms, "27:49:east")
        self.assertRaises(ValueError, parse_dms, ":27:49:23.2:east:")


@patch.object(CSRUtils, 'get_csr')
class TestCRSUtils(TestCase):
    """Test CSR models."""

    def test_parse_geometry_gml_qgis(self):
        """Test parse_gml_geometry for wfs from qgis server."""
        gml_file_path = os.path.join(test_data_directory, 'wfs.xml')
        self.assertTrue(os.path.exists(gml_file_path))
        with open(gml_file_path) as file:
            gml_string = file.read()
            geom = parse_gml_geometry(gml_string)
        self.assertIsNotNone(geom)
        self.assertTrue(geom.valid)
        self.assertEqual(geom.geom_type, 'Polygon')

    def test_parse_geometry_gml_workspace(self):
        """Test parse_gml_geometry with workspace"""
        gml_file_path = os.path.join(test_data_directory, 'wfs_geoserver.xml')
        self.assertTrue(os.path.exists(gml_file_path))
        with open(gml_file_path) as file:
            gml_string = file.read()
            geom = parse_gml_geometry(gml_string, tag_name='kartoza:test')
        self.assertIsNotNone(geom)
        self.assertTrue(geom.valid)
        self.assertEqual(geom.geom_type, 'MultiPolygon')
