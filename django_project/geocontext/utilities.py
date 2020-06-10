import re
import logging

import geopy
import geopy.distance
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


def transform_geometry(geometry: GEOSGeometry, srid_target: int) -> GEOSGeometry:
    """Wrapper to transform geometry x y from srid_source to srid_target if required.

    :param geometry: GEOSGeometry
    :type geometry: GEOSGeometry

    :param srid_target: The target SRID.
    :type srid_target: int

    :return: transformed geometry
    :rtype: GEOSGeometry
    """
    if geometry.srid != srid_target:
        geometry.transform(srid_target)
    return geometry



def simplify_geometry(geometry: GEOSGeometry, tolerance: float) -> GEOSGeometry:
    """Wrapper to simplify geometry using GEOS simplify (Douglas-Peucker). 

    Tolerance accepts meters (search_dist in projection of data makes sense).
    Preserving topology is False to avoid processing overhead

    :param tolerance: meters
    :type tolerance: float

    :return: transformed point
    :rtype: Point
    """
    geometry.simplify(tolerance=tolerance, preserve_topology=False)
    return geometry


def flatten_geometry(geometry: GEOSGeometry) -> GEOSGeometry:
    """Convert 3d geometry to 2d. Ignores if already 2d.

    :param geometry: 3D geometry.
    :type geometry

    :returns: 2D geometry.
    :rtype: geometry
    """
    if geometry.hasz:
        if geometry.geom_type == 'Point':
            geometry = Point(geometry.x, geometry.y, geometry.srid)
        elif geometry.geom_type == 'LineString':
            points = [flatten_geometry(Point(p)) for p in geometry]
            geometry = LineString(points, srid=geometry.srid)
        elif geometry.geom_type == 'LinearRing':
            points = [flatten_geometry(Point(p)) for p in geometry]
            geometry = LinearRing(points, srid=geometry.srid)
        elif geometry.geom_type == 'Polygon':
            linear_rings = [flatten_geometry(p) for p in geometry]
            geometry = Polygon(*linear_rings, srid=geometry.srid)
        elif geometry.geom_type == 'MultiPoint':
            points = [flatten_geometry(p) for p in geometry]
            geometry = MultiPoint(*points, srid=geometry.srid)
        elif geometry.geom_type == 'MultiLineString':
            lines = [flatten_geometry(p) for p in geometry]
            geometry = MultiLineString(*lines, srid=geometry.srid)
        elif geometry.geom_type == 'MultiPolygon':
            polygons = [flatten_geometry(p) for p in geometry]
            geometry = MultiPolygon(*polygons, srid=geometry.srid)
        else:
            raise Exception('Not supported geometry')
    return geometry


def parse_dms(coord: str) -> tuple:
    """Parse DMS input. (Split by °,',", or :)

    :param coord: Coord string
    :type coord: str

    :raises ValueError: If string could not be parsed

    :return: degrees, minutes, seconds
    :rtype: int, int, float
    """
    coord_parts = re.split(r'[°\'"\:]+', coord)
    if len(coord_parts) > 4:
        raise ValueError("Could not parse DMS format input")

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


def get_bbox(point: Point, min_distance: float = 10, order_latlon: bool = True) -> str:
    """
    Get bbox that is guaranteed to be {min_distance} meters from point. BBOX corners will
    be futher but the distance in cardinal directions from point will equal min_distance.
    Lower corner specified first. Lon/lat (x,y) order can be flipped for CRS if needed.

    :param point: Point
    :type point: Point

    :param min_distance: Minimum distance that the bbox should include in meter.
    :type min_distance: float

    :param order_latlon: bbox order depends on CRS.
    :type order_latlon: bool (default True)

    :return: BBOX string: 'lower corner x, lower corner y, upper corner x, upper corner y'
    :rtype: str
    """
    # Distance calculation defaults to WGS84 - converted back if needed
    if point.srid != 4326:
        point = transform_geometry(point, 4326)

    start_point = geopy.Point(longitude=point.x, latitude=point.y)
    distance = geopy.distance.distance(meters=min_distance)

    north = distance.destination(point=start_point, bearing=0)
    east = distance.destination(point=start_point, bearing=90)
    south = distance.destination(point=start_point, bearing=180)
    west = distance.destination(point=start_point, bearing=270)

    lower_left = Point(west.longitude, south.latitude, srid=4326)
    upper_right = Point(east.longitude, north.latitude, srid=4326)

    if point.srid != 4326:
        lower_left = transform_geometry(lower_left, point.srid)
        upper_right = transform_geometry(upper_right, point.srid)

    if order_latlon:
        bbox = [lower_left.x, lower_left.y, upper_right.x, upper_right.y]
    else:
        bbox = [lower_left.y, lower_left.x, upper_right.y, upper_right.x]

    return ','.join([str(i) for i in bbox])
