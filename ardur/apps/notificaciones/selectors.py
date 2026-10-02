from ardur.apps.expedientes.models import Expediente
from ardur.apps.ordenes.models import Orden
from ardur.apps.usuarios.permissions import tiene_rol

VISIBLE = ('LISTO_PARA_NOTIFICAR', 'ASIGNADO_NOTIFICACION', 'NOTIFICADO', 'NO_NOTIFICADO', 'INCIDENCIA')

def expedientes_visibles(usuario):
    qs = Expediente.objects.filter(estado__in=VISIBLE).select_related('orden', 'cliente', 'predio')
    if tiene_rol(usuario, 'JEFE_NOTIFICACIONES', 'CONSULTA'):
        return qs
    if tiene_rol(usuario, 'NOTIFICADOR'):
        return qs.filter(asignacion__usuario_notificador=usuario)
    return qs.none()

def ordenes_visibles(usuario):
    return Orden.objects.filter(expedientes__in=expedientes_visibles(usuario)).distinct()
