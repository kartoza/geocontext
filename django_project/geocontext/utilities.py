# coding=utf-8
"""Utilities module for geocontext app."""

import logging
from xml.dom import minidom

from django.contrib.gis.geos import (
    GEOSGeometry, Point, LineString, LinearRing, Polygon, MultiPoint,
    MultiLineString, MultiPolygon)
from django.contrib.gis.gdal.error import GDALException

logger = logging.getLogger(__name__)


def convert_coordinate(x, y, srid_source, srid_target):
    """Convert coordinate x y from srid_source to srid_target.

    :param x: The value of x coordinate.
    :type x: float

    :param y: The value of y coordinate.
    :type y: float

    :param srid_source: The source SRID.
    :type srid_source: int

    :param srid_target: The target SRID.
    :type srid_target: int

    :return: tuple of converted x and y in float.
    :rtype: tuple(float, float)
    """
    # create a geometry from coordinates
    point = Point(x, y, srid=srid_source)

    point.transform(srid_target)

    return point.x, point.y


def parse_gml_geometry(gml_string, workspace=None):
    """Parse geometry from gml document.

    :param gml_string: String that represent full gml document.
    :type gml_string: unicode

    :returns: GEOGeometry from the gml document, the first one if there are
        more than one.
    :rtype: GEOSGeometry
    """
    xmldoc = minidom.parseString(gml_string)
    try:
        if workspace:
            tag_name = workspace + ':' + 'geom'
            geometry_dom = xmldoc.getElementsByTagName(tag_name)[0]
            geometry_gml_dom = geometry_dom.childNodes[0]
            return GEOSGeometry.from_gml(geometry_gml_dom.toxml())
        else:
            geometry_dom = xmldoc.getElementsByTagName('qgs:geometry')[0]
            geometry_gml_dom = geometry_dom.childNodes[1]
            return GEOSGeometry.from_gml(geometry_gml_dom.toxml())
    except IndexError:
        logger.error('No geometry found')
        return None
    except GDALException:
        logger.error('GDAL error')
        return None


def convert_2d_to_3d(geometry_2d):
    """Convert 2d geometry to 3d with adding z = 0.

    :param geometry_2d: 2D geometry.
    :type geometry

    :returns: 3D geometry with z = 0.
    :rtype: geometry
    """
    if geometry_2d.geom_type == 'Point':
        geometry_3d = Point(geometry_2d.x, geometry_2d.y, 0, geometry_2d.srid)
    elif geometry_2d.geom_type == 'LineString':
        points = [convert_2d_to_3d(Point(p)) for p in geometry_2d]
        geometry_3d = LineString(points, srid=geometry_2d.srid)
    elif geometry_2d.geom_type == 'LinearRing':
        points = [convert_2d_to_3d(Point(p)) for p in geometry_2d]
        geometry_3d = LinearRing(points, srid=geometry_2d.srid)
    elif geometry_2d.geom_type == 'Polygon':
        linear_rings = [convert_2d_to_3d(p) for p in geometry_2d]
        geometry_3d = Polygon(*linear_rings, srid=geometry_2d.srid)
    elif geometry_2d.geom_type == 'MultiPoint':
        points = [convert_2d_to_3d(p) for p in geometry_2d]
        geometry_3d = MultiPoint(*points, srid=geometry_2d.srid)
    elif geometry_2d.geom_type == 'MultiLineString':
        lines = [convert_2d_to_3d(p) for p in geometry_2d]
        geometry_3d = MultiLineString(*lines, srid=geometry_2d.srid)
    elif geometry_2d.geom_type == 'MultiPolygon':
        polygons = [convert_2d_to_3d(p) for p in geometry_2d]
        geometry_3d = MultiPolygon(*polygons, srid=geometry_2d.srid)
    else:
        raise Exception('Not supported geometry')

    return geometry_3d


def get_bbox(x, y, factor=0.001):
    """Get small enough bbox to cover point x,y

    :param x: X coordinate
    :type x: float
    :param y: Y coordinate
    :type y: float
    :param factor: The factor to get the bbox, see the formula.
    :type factor: float

    :return: BBOX as a list [xmin, ymin, xmax, ymax)
    :rtype: list
    """
    x_diff = abs(x * factor)
    y_diff = abs(y * factor)
    return [
        x - x_diff,
        y - y_diff,
        x + x_diff,
        y + y_diff
    ]
