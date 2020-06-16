from django.contrib.gis.geos import Point

from geocontext.models.query import Query


def log_query(query_type: str, key: str, point: Point, tolerance: float):
    """Log API query parameters

    :param query_type: Query type (service, group, collection)
    :type query_type: str
    :param key: Query key (service_key, group_key, collection_key)
    :type key: str
    :param point: Query coordinate
    :type point: Point
    :param tolerance: Tolerance of query.
    :type tolerance: int
    """
    Query.objects.create(
        query_type=query_type,
        key=key,
        geometry=point,
        tolerance=tolerance
    )
