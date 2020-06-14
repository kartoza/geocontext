import json
import re

from arcgis2geojson import arcgis2geojson
import geopy
import geopy.distance
from django.contrib.gis.geos import GEOSGeometry, Point
from multiprocessing import current_process


def flatten(geometry: GEOSGeometry) -> GEOSGeometry:
    """Convert 3d geometry to 2d. Ignores if already 2d.

    :param geometry: 3D geometry.
    :type geometry
    :raises ValueError: If geometry could not be flattened
    :returns: 2D geometry.
    :rtype: geometry
    """
    if geometry.hasz:
        # We use a little Django GEOS hack - ewkt representation removes higher dimensions
        # https://docs.djangoproject.com/en/3.0/ref/contrib/gis/geos/
        geometry = GEOSGeometry(geometry.ewkt)
        if geometry.hasz:
            raise ValueError('Could not flatten 3d geometry')
    return geometry


def get_bbox(point: Point, search_distance: float = 10, order_latlon: bool = True) -> str:
    """
    Get bbox that is guaranteed to be {search_distance} meters from point. BBOX corners
    will be futher but the distance in cardinal directions from point will equal
    search_distance. Lower corner left specified first. Lon/lat (x,y) order can be
    flipped if CRS requires.

    :param point: Point
    :type point: Point
    :param search_distance: Minimum distance that the bbox should include in meter.
    :type search_distance: float
    :param order_latlon: bbox order depends on CRS.
    :type order_latlon: bool (default True)
    :return: BBOX string: 'lower corner x, lower corner y, upper corner x, upper corner y'
    :rtype: str
    """
    original_srid = point.srid
    if original_srid != 4326:
        point = transform(point, 4326)

    start_point = geopy.Point(longitude=point.x, latitude=point.y)
    distance = geopy.distance.distance(meters=search_distance)

    north = distance.destination(point=start_point, bearing=0)
    east = distance.destination(point=start_point, bearing=90)
    south = distance.destination(point=start_point, bearing=180)
    west = distance.destination(point=start_point, bearing=270)

    lower_left = Point(west.longitude, south.latitude, srid=4326)
    upper_right = Point(east.longitude, north.latitude, srid=4326)

    if original_srid != 4326:
        lower_left = transform(lower_left, original_srid)
        upper_right = transform(upper_right, original_srid)

    if order_latlon:
        bbox = [lower_left.x, lower_left.y, upper_right.x, upper_right.y]
    else:
        bbox = [lower_left.y, lower_left.x, upper_right.y, upper_right.x]

    return ','.join([str(i) for i in bbox])


def parse_coord(x: str, y: str, srid: str = '4326') -> float:
    """Parse string DD/DM/DMS coordinate input. Split by °,',".
    Signed degrees or suffix E/W/N/S.

    :param x: (longitude)
    :type x: str
    :param y: Y (latitude)
    :type y: str
    :param srid: SRID (default=4326).
    :type srid: int
    :raises ValueError: If string could not be parsed
    :return: point wih srid
    :rtype: Point
    """
    # Parse srid and create point in crs srid
    try:
        srid = int(srid)
    except ValueError:
        raise ValueError(f"SRID: '{srid}' not valid")

    # Parse Coordinate try DD / otherwise DMS
    cardinals = ['N', 'n', 'E', 'e', 'S', 's', 'W', 'w']
    coords = {'x': x, 'y': y}
    for coord, val in coords.items():
        try:
            sign = 1
            for direction in cardinals:
                for neg_cardinal in ['S', 'W']:
                    if neg_cardinal in val.upper():
                        sign = -1
                val = val.replace(direction, '')
            # Split and get rid of empty space
            coord_parts = [v for v in re.split(r'[°\'"]+', val) if v]
            if len(coord_parts) >= 4:
                raise ValueError('Could not parse DMS format input')
            # Degree, minute, decimal seconds
            elif len(coord_parts) == 3:
                degrees = int(coord_parts[0])
                minutes = int(coord_parts[1])
                seconds = float(coord_parts[2])
            # Degree, decimal minutes
            elif len(coord_parts) == 2:
                degrees = int(coord_parts[0])
                minutes = float(coord_parts[1])
                seconds = 0.0
            # Decimal degree
            elif len(coord_parts) == 1:
                degrees = float(coord_parts[0])
                minutes = 0.0
                seconds = 0.0
            coords[coord] = sign * (degrees + (minutes / 60.0) + (seconds / 3600.0))
        except ValueError:
            raise ValueError(
                f"Coord '{coords[coord]}' parse failed. Only DD, DM, DMS sep=(°,',\")")
    return Point(coords['x'], coords['y'], srid=srid)


def parse_geometry(geometry: dict, arc: bool = False) -> GEOSGeometry:
    """Parse geometry from string or json to GEOSGeometry.
    Large geometries parsed through arcgis could block async.

    :param geometry: Geometry to parse
    :type geometry: dict
    :param geometry: ArcREST format
    :type geometry: bool
    :return: GEOSGeometry geometry
    :rtype: GEOSGeometry
    """
    if isinstance(geometry, GEOSGeometry):
        return geometry
    try:
        if isinstance(geometry, str):
            geometry = json.loads(geometry)
        if arc:
            geos = GEOSGeometry(json.dumps(arcgis2geojson(geometry)))
            return geos
        else:
            return GEOSGeometry(json.dumps(geometry))
    except Exception:
        return None


def transform(geometry: GEOSGeometry, srid_target: int) -> GEOSGeometry:
    """Wrapper to transform geometry x y from srid_source to srid_target if required.

    :param geometry: GEOSGeometry
    :type geometry: GEOSGeometry
    :param srid_target: The target SRID.
    :type srid_target: int
    :raises ValueError: If geometry could not be transformed
    :return: transformed geometry
    :rtype: GEOSGeometry
    """
    if geometry.srid != srid_target:
        geometry = geometry.transform(srid_target, clone=True)
        if geometry.srid != srid_target:
            raise ValueError('Could not transform geometry')
    return geometry
