from django.db import models
from ardur.apps.core.models import Entity

class Cliente(Entity):
    cedula_ruc_original = models.CharField(max_length=100, blank=True)
    cedula_ruc_normalizada = models.CharField(max_length=100, blank=True, db_index=True)
    nombres = models.TextField()
    fallecido = models.BooleanField(default=False)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.nombres
