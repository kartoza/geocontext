import pytest

from django.contrib.gis.geos import Point

from geocontext.utilities.geometry import flatten, parse_coord


def test_flatten_ignore_2d():
    point = Point(1, 2)
    assert point == flatten(point)


def test_parse_coord_DD():
    x = '31.3963'
    y = '-24.4561'
    test = parse_coord(x, y)
    expect = Point(31.3963, -24.4561)
    assert (test.x, test.y) == (expect.x, expect.y)


def test_parse_coord_DMS_direction():
    x = '31°23\'46.7"E'
    y = '24°27\'22.0"S'
    test = parse_coord(x, y)
    expect = Point(31.396305555555553, -24.45611111111111)
    assert (test.x, test.y) == (expect.x, expect.y)


def test_parse_coord_DMS_signed():
    x = '31°23\'46.7"'
    y = '-24°27\'22.0"'
    test = parse_coord(x, y)
    expect = Point(31.396305555555553, -24.45611111111111)
    assert (test.x, test.y) == (expect.x, expect.y)


def test_parse_coord_DM():
    x = '31°23.778E'
    y = '24°27.366S'
    test = parse_coord(x, y)
    expect = Point(31.3963, -24.4561)
    assert (test.x, test.y) == (expect.x, expect.y)


def test_parse_coord_comma_sep():
    x = '31°23,778E'
    y = '24°27,366S'
    test = parse_coord(x, y)
    expect = Point(31.3963, -24.4561)
    assert (test.x, test.y) == (expect.x, expect.y)


def test_parse_coord_invalid_srid():
    x = '31°23,778E'
    y = '24°27,366S'
    srid = '4326WGS84'
    with pytest.raises(ValueError):
        parse_coord(x, y, srid)


def test_parse_coord_invalid_coordinates():
    x = '31°23\'46"731"E'
    y = '24°27\'22.0"S'
    with pytest.raises(ValueError):
        parse_coord(x, y)
