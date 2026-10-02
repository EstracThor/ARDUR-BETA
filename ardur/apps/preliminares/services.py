from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from ardur.apps.usuarios.permissions import exigir_rol
from ardur.apps.documentos.services import sha256, validar_archivo
from ardur.apps.expedientes.models import Expediente
from ardur.apps.auditoria.services import registrar

@transaction.atomic
def registrar_preliminar(expediente_id, usuario, pdf=None, cantidad=None, recargo=None):
    exigir_rol(usuario, 'JEFE_FINANCIERA')
    e = Expediente.objects.select_for_update(of=('self',)).select_related('preliminar').get(pk=expediente_id)
    if e.estado not in ('PENDIENTE_PRELIMINAR', 'PRELIMINAR_GENERADA'):
        raise ValidationError('El expediente no admite registro de preliminar en este estado.')
    p = e.preliminar
    if pdf:
        validar_archivo(pdf, {'.pdf'})
        p.sha256 = sha256(pdf)
        p.archivo_pdf.save(pdf.name, pdf, save=False)
    if recargo is not None and recargo < 0:
        raise ValidationError('Recargo reportado no puede ser negativo.')
    p.estado, p.registrado_por, p.fecha_registro = 'GENERADA', usuario, timezone.now()
    p.cantidad_titulos, p.recargo_reportado = cantidad, recargo
    p.save()
    before = e.estado
    e.estado = 'PRELIMINAR_GENERADA'
    e.save(update_fields=['estado'])
    registrar(usuario, 'CARGA_PRELIMINAR', p, {'sha256': p.sha256, 'recargo_reportado': str(recargo) if recargo is not None else None})
    registrar(usuario, 'CAMBIO_ESTADO', e, antes={'estado': before}, despues={'estado': e.estado})
    return p

@transaction.atomic
def transferir(expediente_id, usuario):
    exigir_rol(usuario, 'JEFE_FINANCIERA')
    e = Expediente.objects.select_for_update(of=('self',)).select_related('preliminar').get(pk=expediente_id)
    if e.estado != 'PRELIMINAR_GENERADA' or e.preliminar.estado != 'GENERADA':
        raise ValidationError('Primero debe registrar la preliminar generada externamente.')
    e.estado = 'LISTO_PARA_NOTIFICAR'
    e.preliminar.estado = 'LISTA_PARA_NOTIFICAR'
    e.preliminar.save(update_fields=['estado'])
    e.save(update_fields=['estado'])
    registrar(usuario, 'CAMBIO_ESTADO', e, antes={'estado': 'PRELIMINAR_GENERADA'}, despues={'estado': e.estado})
    return e
