from django.db import transaction
from django.core.exceptions import ValidationError
from ardur.apps.usuarios.permissions import exigir_rol
from ardur.apps.expedientes.models import Expediente
from ardur.apps.auditoria.services import registrar
from .models import LoteNotificacion, AsignacionNotificador

@transaction.atomic
def crear_lote(orden, fecha, notificador, ids, usuario):
    exigir_rol(usuario, 'JEFE_NOTIFICACIONES')
    if not notificador.is_active or not notificador.groups.filter(name='NOTIFICADOR').exists():
        raise ValidationError('Seleccione un usuario activo del grupo NOTIFICADOR.')
    ids = set(ids)
    cases = list(Expediente.objects.select_for_update().filter(pk__in=ids, orden=orden))
    if not cases or len(cases) != len(ids):
        raise ValidationError('Seleccione expedientes de la misma orden.')
    if any(e.estado != 'LISTO_PARA_NOTIFICAR' or hasattr(e, 'asignacion') for e in cases):
        raise ValidationError('Solo puede asignar expedientes listos y aún no asignados.')
    lote = LoteNotificacion.objects.create(orden=orden, fecha_programada=fecha, responsable=usuario, estado='ASIGNADO')
    registrar(usuario, 'CREACION_LOTE', lote)
    for e in cases:
        a = AsignacionNotificador.objects.create(lote=lote, expediente=e, usuario_notificador=notificador)
        e.estado = 'ASIGNADO_NOTIFICACION'
        e.save(update_fields=['estado'])
        registrar(usuario, 'ASIGNACION_NOTIFICADOR', a, {'notificador': notificador.pk, 'expediente': str(e.pk)})
        registrar(usuario, 'CAMBIO_ESTADO', e, antes={'estado': 'LISTO_PARA_NOTIFICAR'}, despues={'estado': e.estado})
    return lote

@transaction.atomic
def registrar_resultado(asignacion_id, estado, observaciones, usuario):
    exigir_rol(usuario, 'JEFE_NOTIFICACIONES')
    states = {'ENTREGADO': 'NOTIFICADO', 'NO_LOCALIZADO': 'NO_NOTIFICADO', 'INCIDENCIA': 'INCIDENCIA'}
    if estado not in states:
        raise ValidationError('Resultado no válido.')
    initial = AsignacionNotificador.objects.get(pk=asignacion_id)
    lote = LoteNotificacion.objects.select_for_update().get(pk=initial.lote_id)
    a = AsignacionNotificador.objects.select_for_update().get(pk=asignacion_id)
    e = Expediente.objects.select_for_update().get(pk=a.expediente_id)
    if e.estado == 'CERRADO':
        raise ValidationError('No se modifica un expediente cerrado.')
    before = {'estado': a.estado, 'observaciones': a.observaciones}
    a.estado, a.observaciones = estado, observaciones
    a.save(update_fields=['estado', 'observaciones'])
    prev = e.estado
    e.estado = states[estado]
    e.save(update_fields=['estado'])
    lote.estado = 'COMPLETADO' if not lote.asignaciones.filter(estado__in=['PENDIENTE', 'ASIGNADO']).exists() else 'EN_PROCESO'
    lote.save(update_fields=['estado'])
    registrar(usuario, 'RESULTADO_NOTIFICACION', a, antes=before, despues={'estado': estado, 'observaciones': observaciones})
    registrar(usuario, 'CAMBIO_ESTADO', e, antes={'estado': prev}, despues={'estado': e.estado})
    return a
