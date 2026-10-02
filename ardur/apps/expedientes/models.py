from django.db import models
from django.utils import timezone
from ardur.apps.core.models import Entity

class Expediente(Entity):
    orden = models.ForeignKey('ordenes.Orden', on_delete=models.PROTECT, related_name='expedientes')
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.PROTECT)
    predio = models.ForeignKey('catastro.Predio', null=True, blank=True, on_delete=models.PROTECT)
    detalle = models.OneToOneField('financiera.CarteraDetalle', on_delete=models.PROTECT)
    ciu = models.CharField(max_length=100, blank=True, db_index=True)
    suministro = models.CharField(max_length=254, blank=True, db_index=True)
    clave = models.CharField(max_length=254, blank=True, db_index=True)
    numero_negocio = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=40, default='PENDIENTE_PRELIMINAR', db_index=True)
    fecha_apertura = models.DateTimeField(default=timezone.now)
    caso_fingerprint = models.CharField(max_length=64, db_index=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['caso_fingerprint'], condition=~models.Q(estado='CERRADO'), name='expediente_caso_activo_unico')]
    def __str__(self):
        return self.numero_negocio or f'Interno {self.id}'
