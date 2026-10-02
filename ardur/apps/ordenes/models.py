from django.conf import settings
from django.db import models
from ardur.apps.core.models import Entity

class Orden(Entity):
    numero_negocio = models.CharField(max_length=100, null=True, blank=True)
    parroquia = models.CharField(max_length=100)
    zona = models.CharField(max_length=50)
    sector = models.CharField(max_length=50)
    estado = models.CharField(max_length=40, default='ABIERTA')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    def __str__(self):
        return self.numero_negocio or f'Interno {self.id}'
