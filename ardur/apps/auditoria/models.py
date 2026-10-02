from django.conf import settings
from django.db import models
from ardur.apps.core.models import Entity

class EventoAuditoria(Entity):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    accion = models.CharField(max_length=100, db_index=True)
    entidad = models.CharField(max_length=100, db_index=True)
    id_entidad = models.CharField(max_length=100, db_index=True)
    metadata = models.JSONField(default=dict)
    antes = models.JSONField(default=dict)
    despues = models.JSONField(default=dict)
    class Meta:
        ordering = ['-fecha_creacion']
