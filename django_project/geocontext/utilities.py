import logging
from xml.dom import minidom
import xml.etree.ElementTree as ET

from django.contrib.gis.geos import (
    GEOSGeometry, Point, LineString, LinearRing, Polygon,
    MultiPoint, MultiLineString, MultiPolygon
)
from django.contrib.gis.gdal.error import GDALException

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


def convert_coordinate(x: float, y: float, srid_source: int, srid_target: int) -> tuple:
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
    point = Point(x, y, srid=srid_source)
    point.transform(srid_target)
    return point.x, point.y


def parse_gml_geometry(gml_string, tag_name: str = 'qgs:geometry') -> GEOSGeometry:
    """Parse geometry from gml document.

    :param gml_string: String that represent full gml document.
    :type gml_string: unicode

    :param tag_name: gml tag
    :type tag_name: str

    :returns: GEOGeometry from the gml document, the first one if there are
        more than one.
    :rtype: GEOSGeometry
    """
    try:
        xmldoc = minidom.parseString(gml_string)
    except Exception as e:
        logger.error(f'Could not parse GML string: {e}')
        return None
    try:
        if tag_name == 'qgs:geometry':
            geometry_dom = xmldoc.getElementsByTagName(tag_name)[0]
            geometry_gml_dom = geometry_dom.childNodes[1]
            return GEOSGeometry.from_gml(geometry_gml_dom.toxml())
        else:
            tag_name = tag_name.split(':')[0] + ':' + 'geom'
            geometry_dom = xmldoc.getElementsByTagName(tag_name)[0]
            geometry_gml_dom = geometry_dom.childNodes[0]
            return GEOSGeometry.from_gml(geometry_gml_dom.toxml())

    except IndexError:
        logger.error('No geometry found')
        return None
    except GDALException:
        logger.error('GDAL error')
        return None


def tag_with_version(tag: str, version: str) -> str:
    """ Replace version in tag

    :return: tag
    :rtype: str
    """
    if version:
        return version + tag
    return tag


def find_geometry_in_xml(content: str) -> tuple:
    """Find geometry in xml string

    :param content: xml content
    :type content: str
    :return: geometry name and geometry type
    :rtype: tuple
    """
    content_parsed = ET.fromstring(content)
    version = None
    try:
        content_parsed.tag.split('}')[1]
        version = content_parsed.tag.split('}')[0] + '}'
    except IndexError:
        pass
    geometry_name, geometry_type = None, None
    try:
        complex_type = content_parsed.find(
            tag_with_version('complexType', version))
        complex_content = complex_type.find(
            tag_with_version('complexContent', version))
        extension = complex_content.find(
            tag_with_version('extension', version))
        sequences = extension.find(
            tag_with_version('sequence', version))
        for sequence in sequences:
            try:
                if 'gml' in sequence.attrib['type']:
                    geometry_name = sequence.attrib['name']
                    geometry_type = sequence.attrib['type'].replace(
                        'gml:', '').replace('PropertyType', '')
            except KeyError:
                continue
        pass
    except Exception as e:
        logging.exception(e)
        pass
    return geometry_name, geometry_type


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


def get_bbox(x: float, y: float, precision: float = 0.0001) -> list:
    """Get small enough bbox to cover point x,y
    precision of 4 == ~10 m bounding box

    :param x: X coordinate
    :type x: float
    :param y: Y coordinate
    :type y: float
    :param precision: The factor to get the bbox, see the formula.
    :type precision: float

    :return: BBOX as a list [xmin, ymin, xmax, ymax)
    :rtype: list
    """
    return [
        x - precision,
        y - precision,
        x + precision,
        y + precision
    ]


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
