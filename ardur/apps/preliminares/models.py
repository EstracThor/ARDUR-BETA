from django.conf import settings
from django.db import models
from ardur.apps.core.models import Entity

class Preliminar(Entity):
    expediente = models.OneToOneField('expedientes.Expediente', on_delete=models.PROTECT, related_name='preliminar')
    estado = models.CharField(max_length=30, default='PENDIENTE_CABILDO')
    archivo_pdf = models.FileField(upload_to='preliminares/%Y/%m/', blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    cantidad_titulos = models.PositiveIntegerField(null=True, blank=True)
    recargo_reportado = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    fuente = models.CharField(max_length=30, default='ERP_CABILDO', editable=False)

class ReglaRecargo(Entity):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    configuracion = models.JSONField(default=dict)
    # Reservada para definición futura; no se aplica a deudas ni preliminares.
