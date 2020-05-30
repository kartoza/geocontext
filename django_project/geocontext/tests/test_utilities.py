import os

from django.test import SimpleTestCase
from geocontext.utilities import (
    convert_coordinate, parse_gml_geometry, get_bbox)

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')


class TestUtilities(SimpleTestCase):
    """Test for utilities module."""

    def test_convert_coordinate(self):
        """Test convert_coordinate method."""
        result = convert_coordinate(1, 1, 4326, 3857)
        self.assertAlmostEqual(result[0], 111319.49, places=2)
        self.assertAlmostEqual(result[1], 111325.14, places=2)

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

    def test_get_bbox(self):
        """Test get_bbox function."""
        bbox = get_bbox(1, 10, 0.0001)
        self.assertEqual([0.9999, 9.999, 1.0001, 10.001], bbox)
        self.assertLess(bbox[0], bbox[2])
        self.assertLess(bbox[1], bbox[3])

        bbox = get_bbox(-1, -10, 0.0001)
        self.assertLess(bbox[0], bbox[2])
        self.assertLess(bbox[1], bbox[3])
