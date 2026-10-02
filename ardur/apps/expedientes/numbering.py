from django.conf import settings
from django.utils.module_loading import import_string

def numero_expediente(valor=None):
    return import_string(settings.CASE_NUMBERING_STRATEGY)(valor)
