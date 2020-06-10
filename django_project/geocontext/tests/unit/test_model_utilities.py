import os

from django.contrib.gis.geos import Point
from django.test import SimpleTestCase
from geocontext.utilities import (
    transform_geometry,
    dms_dd,
    get_bbox,
    parse_dms,
)

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')


class TestUtilities(SimpleTestCase):
    """Test for utilities module."""

    def test_transform_geometry(self):
        """Test transform_geometry method."""
        result = transform_geometry(Point(1, 1, srid=4326), 3857)
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
