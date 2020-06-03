from decimal import Decimal
import logging

from django.contrib.gis.geos import (
    GEOSGeometry, Point, LineString, LinearRing, Polygon,
    MultiPoint, MultiLineString, MultiPolygon
)

logger = logging.getLogger(__name__)


class ServiceDefinitions():
    """Class storing service definitions"""
    WFS = 'WFS'
    WCS = 'WCS'
    WMS = 'WMS'
    REST = 'REST'
    ARCREST = 'ArcREST'
    WIKIPEDIA = 'Wikipedia'
    PLACENAME = 'PlaceName'
    QUERY_TYPES = (
        (WFS, 'WFS'),
        (WCS, 'WCS'),
        (WMS, 'WMS'),
        (REST, 'REST'),
        (ARCREST, 'ArcREST'),
        (WIKIPEDIA, 'Wikipedia'),
        (PLACENAME, 'PlaceName'),
    )


def convert_2d_to_3d(geometry_2d: GEOSGeometry) -> GEOSGeometry:
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


def convert_coordinate(point, srid_target: int) -> Point:
    """Convert coordinate x y from srid_source to srid_target.

    :param point: Point
    :type point: Point

    :param srid_target: The target SRID.
    :type srid_target: int

    :return: transformed point
    :rtype: Point
    """
    point.transform(srid_target)
    return point


def parse_dms(coord: str) -> tuple:
    """Parse ':' seperated degree:minute:second:direction input.

    :param coord: Coord string
    :type coord: str
    :raises ValueError: If string could not be parsed
    :return: degrees, minutes, seconds
    :rtype: int, int, float
    """
    coord_parts = coord.split(':')
    if len(coord_parts) > 4:
        raise ValueError("Could not parse DMS format input (need dd:mm:ss:DIRECTION")

    degrees = int(coord_parts[0])
    minutes = int(coord_parts[1])
    seconds = float(coord_parts[2])
    direction = coord_parts[3]
    if direction.upper() in ['N', 'E', 'W', 'S']:
        degrees = degrees * -1 if direction.upper() in ['W', 'S'] else degrees
    else:
        raise ValueError("Could not parse DMS format input: (need dd:mm:ss:DIRECTION")
    return degrees, minutes, seconds


def dms_dd(degrees: int, minutes: int = 0, seconds: int = 0.0) -> float:
    """Convert degree minute second to decimal degree

    :param degrees: degrees
    :type degrees: int
    :param minutes: minutes, defaults to 0.0
    :type minutes: int, optional
    :param seconds: seconds, defaults to 0.0
    :type seconds: float, optional

    :return: decimal degree
    :rtype: float
    """
    if degrees >= 0:
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    else:
        decimal = degrees - (minutes / 60.0) - (seconds / 3600.0)
    return decimal


def round_point(point: Point, decimals: int = 4) -> str:
    """Get small enough bbox to cover point x,y

    precision of 4 == ~10 m on srid=4326 bounding box

    :param point: Point
    :type point: Point

    :param precision: Decimals to round
    :type precision: int (default = 4)

    :return: point
    :rtype: Point
    """
    # Bbox generated in WGS84 for consistent boundingbox and transformed back if needed
    original_srid = point.srid
    if original_srid != 4326:
        point = convert_coordinate(point, 4326)

    x_round = Decimal(point.x).quantize(Decimal('0.' + '0' * decimals))
    y_round = Decimal(point.y).quantize(Decimal('0.' + '0' * decimals))
    point = Point(float(x_round), float(y_round), srid=point.srid)

    if original_srid != 4326:
        point = convert_coordinate(point, original_srid)

    return point


def get_bbox(point: Point, precision: float = 0.0001, string: True = bool) -> str:
    """Get small enough bbox to cover point x,y

    precision of 4 == ~10 m on srid=4326 bounding box

    :param point: Point
    :type point: Point

    :param precision: The factor to get the bbox, see the formula.
    :type precision: float

    :param string: Should output be a ',' seperated string - else list
    :type string: bool

    :return: BBOX string
    :rtype: str
    """
    original_srid = point.srid
    # Bbox generated in WGS84 for consistent boundingbox and transformed back if needed
    if original_srid != 4326:
        point = convert_coordinate(point, 4326)

    bbox_min = Point((point.x - precision), (point.y - precision), srid=4326)
    bbox_max = Point((point.x + precision), (point.y + precision), srid=4326)

    if original_srid != 4326:
        bbox_min = convert_coordinate(bbox_min, original_srid)
        bbox_max = convert_coordinate(bbox_max, original_srid)

    bbox = [bbox_min.x, bbox_min.y, bbox_max.x, bbox_max.y]

    if string:
        return ','.join([str(i) for i in bbox])
    else:
        return bbox
