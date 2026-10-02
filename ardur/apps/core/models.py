import uuid
from django.db import models

class Entity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    class Meta:
        abstract = True
