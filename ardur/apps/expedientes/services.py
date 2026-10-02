from django.db import transaction
from django.core.exceptions import ValidationError
from ardur.apps.usuarios.permissions import exigir_rol
from ardur.apps.auditoria.services import registrar
from .models import Expediente
from .numbering import numero_expediente

@transaction.atomic
def actualizar_numero(expediente_id, numero, usuario):
    exigir_rol(usuario, 'JEFE_FINANCIERA')
    e = Expediente.objects.select_for_update().get(pk=expediente_id)
    before = e.numero_negocio
    e.numero_negocio = numero_expediente(numero)
    e.save(update_fields=['numero_negocio'])
    registrar(usuario, 'NUMERO_EXPEDIENTE', e, antes={'numero': before}, despues={'numero': e.numero_negocio})
    return e

@transaction.atomic
def cerrar(expediente_id, motivo, usuario):
    exigir_rol(usuario, 'JEFE_FINANCIERA')
    e = Expediente.objects.select_for_update().get(pk=expediente_id)
    if not motivo.strip():
        raise ValidationError('Se requiere motivo de cierre.')
    if hasattr(e, 'asignacion') and e.asignacion.estado == 'ASIGNADO':
        raise ValidationError('Registre el resultado del lote antes de cerrar el proceso.')
    before = e.estado
    e.estado = 'CERRADO'
    e.save(update_fields=['estado'])
    registrar(usuario, 'CAMBIO_ESTADO', e, {'motivo': motivo}, {'estado': before}, {'estado': e.estado})
    return e
