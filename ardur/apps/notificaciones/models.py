from django.conf import settings
from django.db import models
from ardur.apps.core.models import Entity

class LoteNotificacion(Entity):
    fecha_programada = models.DateField()
    orden = models.ForeignKey('ordenes.Orden', on_delete=models.PROTECT, related_name='lotes')
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    estado = models.CharField(max_length=30, default='PENDIENTE')

class AsignacionNotificador(Entity):
    lote = models.ForeignKey(LoteNotificacion, on_delete=models.PROTECT, related_name='asignaciones')
    expediente = models.OneToOneField('expedientes.Expediente', on_delete=models.PROTECT, related_name='asignacion')
    usuario_notificador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    estado = models.CharField(max_length=30, default='ASIGNADO')
    observaciones = models.TextField(blank=True)
