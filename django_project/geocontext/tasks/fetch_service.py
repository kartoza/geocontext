import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="fetch_service_data")
def fetch_service_data(service_id: str, x: str, y: str):
    from geocontext.models.service import Service
    from geocontext.utilities.geometry import parse_coord
    from geocontext.utilities.async_service import async_retrieve_services
    from geocontext.utilities.async_service import AsyncService

    service = Service.objects.get(id=service_id)
    point = parse_coord(
        x=x, y=y, srid=service.srid)
    async_service = AsyncService(
        service.key, point, service.tolerance)
    new_async_service = async_retrieve_services([async_service])
    if new_async_service[0].value != service.test_value:
        service.status = False
        logger.warning(f'Service: {service.name} status offline')
    else:
        service.status = True
        logger.info(f'Service: {service.name} status online')
    service.save()
