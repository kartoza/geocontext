import pytest

from django.contrib.gis.geos import Point

from geocontext.utilities.worker import Worker


@pytest.mark.django_db
def test_wms():
    point = Point(31.3963, -24.4561, srid=4326)
    expect = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "",
                "geometry": None,
                "properties": {
                    "GRAY_INDEX": 441
                }
            }
        ],
        "totalFeatures": "unknown",
        "numberReturned": 1,
        "timeStamp": "2020-07-06T17:32:08.024Z",
        "crs": None
    }
    data = Worker('service', 'altitude', point, 10, 'json').retrieve_all()
    assert data == expect
