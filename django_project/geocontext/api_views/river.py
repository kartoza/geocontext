import psycopg2

from django.http import Http404
from django.conf import settings
from rest_framework import views
from rest_framework.response import Response


class RiverNameAPIView(views.APIView):
    """Retrieving river name matching: x (long), y (lat).
    """
    def get(self, request, x, y):
        db_name = settings.RIVER_DATABASE['NAME']
        db_host = settings.RIVER_DATABASE['HOST']
        db_user = settings.RIVER_DATABASE['USER']
        db_pass = settings.RIVER_DATABASE['PASSWORD']
        db_port = 5432
        if not db_name or not db_host:
            raise Http404()
        try:
            conn = (
                psycopg2.connect(
                    f"dbname={db_name} user={db_user} host={db_host}"
                    f" password='{db_pass}' port={db_port}"
                )
            )
        except psycopg2.OperationalError:
            raise Http404()
        cursor = conn.cursor()
        cursor.callproc('finder', [x, y])
        results = cursor.fetchone()
        cursor.close()
        if results:
            return Response(results[0])
        else:
            raise Http404()
