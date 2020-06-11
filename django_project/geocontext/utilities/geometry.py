import re

import geopy
import geopy.distance
from django.contrib.gis.geos import GEOSGeometry, Point


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
        geometry.transform(srid_target)
        if geometry.srid != srid_target:
            raise ValueError("Could not transform geometry")
    return geometry


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
            raise ValueError("Could not flatten 3d geometry")
    return geometry


def parse_coord(x: str, y: str, srid: int = 4326) -> float:
    """Parse string DD/DM/DMS coordinate input. Split by °,',", or ':'.

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
    coords = {'x': x, 'y': y}
    for coord, val in coords.items():
        try:
            coord_parts = re.split(r'[°\'"]+', val)
            if len(coord_parts) >= 4:
                raise ValueError("Could not parse DMS format input")
            # DMS
            elif len(coord_parts) == 3:
                degrees = int(coord_parts[0])
                minutes = int(coord_parts[1])
                seconds = float(coord_parts[2])
            # DM
            elif len(coord_parts) == 2:
                degrees = int(coord_parts[0])
                minutes = float(coord_parts[1])
                seconds = 0.0
            # DD
            elif len(coord_parts) == 1:
                degrees = float(coord_parts[0])
                minutes = 0.0
                seconds = 0.0
            coords[coord] = degrees + (minutes / 60.0) + (seconds / 3600.0)
        except ValueError:
            raise ValueError(
                f"Coord '{coords[coord]}' parse failed.")

    return Point(coords['x'], coords['y'], srid=srid)


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
        point = transform(point, 4326)

    start_point = geopy.Point(longitude=point.x, latitude=point.y)
    distance = geopy.distance.distance(meters=min_distance)

    north = distance.destination(point=start_point, bearing=0)
    east = distance.destination(point=start_point, bearing=90)
    south = distance.destination(point=start_point, bearing=180)
    west = distance.destination(point=start_point, bearing=270)

    lower_left = Point(west.longitude, south.latitude, srid=4326)
    upper_right = Point(east.longitude, north.latitude, srid=4326)

    if point.srid != 4326:
        lower_left = transform(lower_left, point.srid)
        upper_right = transform(upper_right, point.srid)

    if order_latlon:
        bbox = [lower_left.x, lower_left.y, upper_right.x, upper_right.y]
    else:
        bbox = [lower_left.y, lower_left.x, upper_right.y, upper_right.x]

    return ','.join([str(i) for i in bbox])
