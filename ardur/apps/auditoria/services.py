from .models import EventoAuditoria

def registrar(usuario, accion, entidad, metadata=None, antes=None, despues=None):
    return EventoAuditoria.objects.create(usuario=usuario, accion=accion, entidad=entidad._meta.label, id_entidad=str(entidad.pk), metadata=metadata or {}, antes=antes or {}, despues=despues or {})
