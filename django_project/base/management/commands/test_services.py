import logging

from django.core.management.base import BaseCommand

from geocontext.models.service import Service
from geocontext.utilities.service import retrieve_service_value, ServiceUtil
from geocontext.utilities.geometry import parse_coord

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to test service status to be run as cron."""

    help = 'Test status of all services'

    def handle(self, *args, **options):
        services = Service.objects.all()
        for service in services:
            point = parse_coord(x=service.x, y=service.y, srid=service.srid)
            service_util = ServiceUtil(service.key, point, service.tolerance)
            new_service_util = retrieve_service_value([service_util])
            if new_service_util.value != service.test_value:
                service.status = False
                logger.warning(f'Service: {service.name} status offline')
            else:
                service.status = True
                logger.info(f'Service: {service.name} status online')
            service.save()
