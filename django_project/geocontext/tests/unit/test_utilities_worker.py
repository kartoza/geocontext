from django.contrib.gis.geos import Point

from geocontext.utilities.geometry import flatten


def test_flatten_ignore_2d():
    point = Point(1, 2)
    assert point == flatten(point)
