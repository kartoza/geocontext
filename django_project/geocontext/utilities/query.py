from django.contrib.gis.geos import Point

from geocontext.models.query import Query


def log_query(type: str, key: str, point: Point, tolerance: float):
    """Log API query parameters

    :param type: Query type (service, group, collection)
    :type type: str
    :param key: Query key (service_key, group_key, collection_key)
    :type key: str
    :param point: Query coordinate
    :type point: Point
    :param tolerance: Tolerance of query.
    :type tolerance: int
    """
    query = Query(
        query_type=type,
        key=key,
        geometry=point,
        tolerance=tolerance
    )
    query.save()
