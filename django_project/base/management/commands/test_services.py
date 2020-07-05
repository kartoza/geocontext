import logging

from django.core.management.base import BaseCommand

from geocontext.models.service import Service
from geocontext.utilities.service import async_retrieve_services, AsyncService
from geocontext.utilities.geometry import parse_coord

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to test service status to be run as cron."""

    help = 'Test status of all services'

    def handle(self, *args, **options):
        services = Service.objects.all()
        for service in services:
            point = parse_coord(x=service.x, y=service.y, srid=service.srid)
            async_service = AsyncService(service.key, point, service.tolerance)
            new_async_service = async_retrieve_services([async_service])
            if new_async_service[0].value != service.test_value:
                service.status = False
                logger.warning(f'Service: {service.name} status offline')
            else:
                service.status = True
                logger.info(f'Service: {service.name} status online')
            service.save()
