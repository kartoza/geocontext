from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from geocontext.models import Service, Group, Collection
from geocontext.serializers.collection import CollectionSerializer
from geocontext.serializers.group import GroupSerializer
from geocontext.serializers.service import ServiceSerializer
from geocontext.throttling import UserTierRateThrottle
from geocontext.utilities.worker import Worker
from geocontext.utilities.geometry import parse_coord
from geocontext.authentication import CustomTokenAuthentication


class GenericAPIView(APIView):
    """Geocontext API v2 endpoint for collection queries.
    Basic query validation, log query, get data and return results.
    """
    throttle_classes = [UserTierRateThrottle]
    authentication_classes = [CustomTokenAuthentication]

    def get(self, request):
        try:
            key = request.GET.get('key', None)
            x = request.GET.get('x', None)
            y = request.GET.get('y', None)
            if None in [key, x, y]:
                raise KeyError('Required request argument ('
                               'registry, key, x, y) missing.')

            srid = request.GET.get('srid', 4326)

            try:
                tolerance = float(request.GET.get('tolerance', 10.0))
            except ValueError:
                raise ValueError('Tolerance should be a float')

            registry = request.GET.get('registry', '')
            if registry.lower() not in ['collection', 'service', 'group']:
                raise ValueError('Registry should be "collection", '
                                 '"service" or "group".')

            outformat = request.GET.get('outformat', 'geojson').lower()
            if outformat not in ['geojson', 'json']:
                raise ValueError('Output format should be either '
                                 'json or geojson')

            point = parse_coord(x, y, srid)
            data = Worker(
                registry, key, point, tolerance, outformat).retrieve_all()
            return Response(data, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegistryAPIView(APIView):
    """
    Fetch list of group or collection
    """

    def get(self, request):

        registry = request.GET.get('registry', None)
        if registry is None:
            raise KeyError('Required request argument (registry) missing.')

        elif registry.lower() not in ['collection', 'service', 'group']:
            raise ValueError('Registry should be "collection", '
                             '"service" or "group".')
        elif registry == 'service':
            services = Service.objects.all()
            return Response(ServiceSerializer(services, many=True).data)

        elif registry == 'group':
            groups = Group.objects.all()
            return Response(GroupSerializer(groups, many=True).data)

        else:
            collections = Collection.objects.all()
            return Response(CollectionSerializer(collections, many=True).data)
