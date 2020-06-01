from distutils.util import strtobool

from rest_framework import views
from rest_framework.response import Response

from geocontext.models.csr import CSR
from geocontext.serializers.cache import CacheGeoJSONSerializer, CacheSerializer
from geocontext.models.utilities import CSRUtils


class CacheListAPI(views.APIView):
    """Retrieving values from cache matching:
    x (long), y (lat) and optional SRID var (default use: 4326)
    """
    def get(self, request, x, y, srid=4326):
        csr_list = CSR.objects.all()
        csr_keys = [o.key for o in csr_list]
        caches = []
        try:
            for csr_key in csr_keys:
                csr_util = CSRUtils(csr_key, x, y, srid)
                cache = csr_util.retrieve_cache()
                caches.append(cache)
        except Exception as e:
            return Response(f'Server exception: {e}')
        if None in caches:
            return Response('No cache found')
        with_geometry = self.request.query_params.get('with-geometry', 'True')
        if strtobool(with_geometry):
            serializer = CacheGeoJSONSerializer(caches, many=True)
        else:
            serializer = CacheSerializer(caches, many=True)
        return Response(serializer.data)
