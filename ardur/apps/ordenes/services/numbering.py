from django.conf import settings
from django.utils.module_loading import import_string

def manual(valor=None):
    """Estrategia beta: solo un número oficial ingresado explícitamente; UUID interno siempre disponible."""
    return str(valor).strip() or None if valor is not None else None

def numero_oficial(valor=None):
    return import_string(settings.ORDER_NUMBERING_STRATEGY)(valor)
