from distutils.util import strtobool

from rest_framework import views
from rest_framework.response import Response

from geocontext.models.service_registry import ContextServiceRegistry
from geocontext.serializers.cache import (
    ContextValueGeoJSONSerializer, ContextValueSerializer)
from geocontext.models.utilities import CSRUtils


class ContextCacheValueListAPI(views.APIView):
    """List all current context cache based on point (x, y)."""

    def get(self, request, x, y, csr_keys=None):
        # Parse location
        x = float(x)
        y = float(y)
        # List all CSR keys
        if not csr_keys:
            csr_list = ContextServiceRegistry.objects.all()
            csr_keys = [o.key for o in csr_list]
        else:
            csr_keys = csr_keys.split(',')

        caches = []
        for csr_key in csr_keys:
            csr_util = CSRUtils(csr_key, x, y)
            cache = csr_util.retrieve_cache()
            caches.append(cache)
        if None in caches:
            return Response('No cache found')
        with_geometry = self.request.query_params.get('with-geometry', 'True')
        if strtobool(with_geometry):
            serializer = ContextValueGeoJSONSerializer(caches, many=True)
        else:
            serializer = ContextValueSerializer(caches, many=True)
        return Response(serializer.data)
