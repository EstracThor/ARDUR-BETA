import logging
from celery import shared_task
from .models import ImportacionCartera

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def procesar_importacion(self, importacion_id):
    from .services import procesar
    try:
        return procesar(importacion_id)
    except Exception as exc:
        logger.exception('Falló la importación %s', importacion_id)
        ImportacionCartera.objects.filter(pk=importacion_id).update(estado='ERROR', error=f'{type(exc).__name__}: {exc}'[:4000])
        raise
