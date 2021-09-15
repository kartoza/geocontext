"""
Module containing controlling Worker class and methods for gathering results
"""
from datetime import datetime as dt
from json import loads
from pytz import UTC
import logging

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models.query import QuerySet
from calendar import month_name
from django.db.models import Q

from geocontext.models.cache import Cache
from geocontext.models.collection import Collection
from geocontext.models.group import Group
from geocontext.models.log import Log
from geocontext.models.service import Service
from geocontext.serializers.cache import CacheSerializer
from geocontext.serializers.collection import NestedCollectionSerializer
from geocontext.serializers.group import NestedGroupSerializer
from geocontext.utilities.geometry import transform, flatten
from geocontext.utilities.async_service import async_retrieve_services, AsyncService

from django.db.models import Value, CharField, Case, When
from django.db.models.functions import StrIndex, Reverse, Right, Replace
from django.contrib.postgres.fields import ArrayField

logger = logging.getLogger(__name__)
MONTHS = list(map(lambda x: x.lower(), list(month_name)[1:]))


class Worker():
    """
    Worker class responsible for retrieving all data from cache or from external
    """

    def __init__(self, registry: str, key: str, point: Point,
                 tolerance: float, outformat: str):
        """Init method for worker class.

        :param key: Service, Group or Collection key.
        :type key: str
        :param point: GEOS query point
        :type point: Point
        :param tolerance: Tolerance to search around point (in meteres)
        :type tolerance: float
        :param outformat: Output format
        :type outformat: str
        """
        self.registry = registry
        self.key = key
        self.point = point
        self.tolerance = tolerance
        self.outformat = outformat
        self.log_request()

    def retrieve_all(self) -> dict:
        """Retrieve all service values matching query from cache - or request externally.

        :return: Serialized cache in out_format
        :rtype: dict
        """
        services = self.get_services()
        caches = self.retrieve_caches(services)
        req_s = services.exclude(key__in=[cache.service.key for cache in caches])

        if len(req_s) > 0:
            async_services = [AsyncService(s, self.point, self.tolerance) for s in req_s]
            new_async_services = async_retrieve_services(async_services)
            caches.extend(self.bulk_create_caches(new_async_services))

        if self.outformat == 'json':
            return self.nest_caches(caches)
        elif self.outformat == 'geojson':
            return self.to_geojson(self.nest_caches(caches))
        else:
            raise ValueError(f'Output format "{self.outformat}" not supported')

    def log_request(self):
        """Log query"""
        Log.objects.create(
            registry=self.registry,
            key=self.key,
            geometry=self.point,
            tolerance=self.tolerance,
            output_format=self.outformat
        )

    def get_services(self) -> Service:
        """Return all services associated with a key from service/group/collection registries.

        :return: Queryset with Service objects
        :rtype: Service
        """
        if self.registry == 'service':
            return Service.objects.filter(key=self.key)
        elif self.registry == 'group':
            services = Service.objects.filter(group__key=self.key)
            return self.order_by_month(services)

        elif self.registry == 'collection':
            services = Service.objects.filter(group__collection__key=self.key)
            return self.order_by_month(services)
            # return services
        else:
            raise ValueError(f'Registry "{self.registry}" not supported')

    def retrieve_caches(self, services: QuerySet) -> list:
        """Retrieve valid caches that are within the tolerance distance of point.
        Single cache is returned per service that is the closest to the point.

        https://stackoverflow.com/questions/20582966/django-order-by-filter-with-distinct

        :param services: Service QuerySet
        :type services: QuerySet
        :return: List of caches
        :rtype: list
        """
        return list(Cache.objects.filter(
            geometry__dwithin=(self.point, self.tolerance),
            service__in=services,
            expired_time__gte=dt.utcnow().replace(tzinfo=UTC)
        ).annotate(
            distance=Distance('geometry', self.point),
            last_subsrt=Right('service__key', StrIndex(Reverse('service__key'), Value('_')) - 1,
                              output_field=CharField()),
        ).annotate(
            key_formatted=Case(
                When(last_subsrt=MONTHS[0],
                     then=Replace('service__key',
                                  Right('service__key', StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('01'),
                                  output_field=CharField()
                                  )),
                When(last_subsrt=MONTHS[1],
                     then=Replace('service__key',
                                  Right('service__key',
                                        StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('02'),
                                  output_field=CharField())),
                When(last_subsrt=MONTHS[2],
                     then=Replace('service__key',
                                  Right('service__key',
                                        StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('03'),
                                  output_field=CharField())),
                When(last_subsrt=MONTHS[3],
                     then=Replace('service__key',
                                  Right('service__key',
                                        StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('04'),
                                  output_field=CharField())),
                When(last_subsrt=MONTHS[4],
                     then=Replace('service__key',
                                  Right('service__key',
                                        StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('05'),
                                  output_field=CharField())),
                When(last_subsrt=MONTHS[5],
                     then=Replace('service__key',
                                  Right('service__key',
                                        StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('06'),
                                  output_field=CharField())),
                When(last_subsrt=MONTHS[6],
                     then=Replace('service__key',
                                  Right('service__key',
                                        StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('07'),
                                  output_field=CharField())),
                When(last_subsrt=MONTHS[7],
                     then=Replace('service__key',
                                  Right('service__key',
                                        StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('08'),
                                  output_field=CharField())),
                When(last_subsrt=MONTHS[8],
                     then=Replace('service__key',
                                  Right('service__key',
                                        StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('09'),
                                  output_field=CharField())),
                When(last_subsrt=MONTHS[9],
                     then=Replace('service__key',
                                  Right('service__key',
                                        StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('10'),
                                  output_field=CharField())),
                When(last_subsrt=MONTHS[10],
                     then=Replace('service__key',
                                  Right('service__key',
                                        StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('11'),
                                  output_field=CharField())),
                When(last_subsrt=MONTHS[11],
                     then=Replace('service__key',
                                  Right('service__key',
                                        StrIndex(Reverse('service__key'), Value('_')) - 1),
                                  Value('12'),
                                  output_field=CharField())),
                default=Replace('service__key',
                                Right('service__key', StrIndex(Reverse('service__key'), Value('_')) - 1),
                                Right('service__key', StrIndex(Reverse('service__key'), Value('_')) - 1),
                                output_field=CharField()),
                output_field=CharField()

            )
        ).order_by(
            'key_formatted', 'distance'
        ).distinct(
            'key_formatted',
        ))

    def bulk_create_caches(self, new_async_services: list) -> list:
        """Bulk update cache with new AsyncService values.

        :param new_async_services: list of service util with values
        :type new_async_services: list
        :return: list of new caches
        :rtype: list
        """
        cache_list = []
        for async_services in new_async_services:
            cache_list.append(Cache(
                service=async_services.service,
                name=async_services.key,
                value=async_services.value,
                created_time=dt.utcnow().replace(tzinfo=UTC),
                expired_time=async_services.expire,
                source_uri=async_services.source_uri,
                geometry=flatten(transform(async_services.geometry, Cache.srid))
            ))
        return Cache.objects.bulk_create(cache_list)

    def nest_caches(self, caches: list) -> dict:
        """Prepare serialized cache representation in nested output format.

        :param caches: list of caches to nest
        :type caches: str
        :return: json with nested services
        :rtype: dict
        """
        serial = {}
        if self.registry == 'service':
            serial = CacheSerializer(caches[0]).data
        elif self.registry == 'group':
            serial = NestedGroupSerializer(Group.objects.get(key=self.key)).data
            serial['services'] = [CacheSerializer(cache).data for cache in caches]
        elif self.registry == 'collection':
            serial = NestedCollectionSerializer(Collection.objects.get(key=self.key)).data
            group_serials = []
            for group_key in serial['groups']:
                group = Group.objects.get(key=group_key)
                group_serial = NestedGroupSerializer(group).data
                group_services = group.services.all()
                caches_filt = [c for c in caches if c.service in group_services]
                group_serial['services'] = [CacheSerializer(c).data for c in caches_filt]
                group_serials.append(group_serial)
            serial['groups'] = group_serials
        return serial

    def to_geojson(self, serial: dict) -> dict:
        """
        Add json data to geojson properties
        """
        return {
            'type': 'Feature',
            'properties': serial,
            'geometry': loads(self.point.json)
        }

    def order_by_month(self, services):
        """
        Ordering services by month
        """
        # filters = Q()
        return services.annotate(
            last_subsrt=Right('key', StrIndex(Reverse('key'), Value('_')) - 1, output_field=CharField()),
        ).annotate(
            key_formatted=Case(
                When(last_subsrt=MONTHS[0], then=Replace('key',
                                                         Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                         Value('01'),
                                                         output_field=CharField()
                                                         )),
                When(last_subsrt=MONTHS[1], then=Replace('key',
                                                         Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                         Value('02'),
                                                         output_field=CharField())),
                When(last_subsrt=MONTHS[2], then=Replace('key',
                                                         Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                         Value('03'),
                                                         output_field=CharField())),
                When(last_subsrt=MONTHS[3], then=Replace('key',
                                                         Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                         Value('04'),
                                                         output_field=CharField())),
                When(last_subsrt=MONTHS[4], then=Replace('key',
                                                         Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                         Value('05'),
                                                         output_field=CharField())),
                When(last_subsrt=MONTHS[5], then=Replace('key',
                                                         Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                         Value('06'),
                                                         output_field=CharField())),
                When(last_subsrt=MONTHS[6], then=Replace('key',
                                                         Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                         Value('07'),
                                                         output_field=CharField())),
                When(last_subsrt=MONTHS[7], then=Replace('key',
                                                         Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                         Value('08'),
                                                         output_field=CharField())),
                When(last_subsrt=MONTHS[8], then=Replace('key',
                                                         Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                         Value('09'),
                                                         output_field=CharField())),
                When(last_subsrt=MONTHS[9], then=Replace('key',
                                                         Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                         Value('10'),
                                                         output_field=CharField())),
                When(last_subsrt=MONTHS[10], then=Replace('key',
                                                          Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                          Value('11'),
                                                          output_field=CharField())),
                When(last_subsrt=MONTHS[11], then=Replace('key',
                                                          Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                                          Value('12'),
                                                          output_field=CharField())),
                default=Replace('key',
                                Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                Right('key', StrIndex(Reverse('key'), Value('_')) - 1),
                                output_field=CharField()),
                output_field=CharField()

            )
        ).order_by('key_formatted')
