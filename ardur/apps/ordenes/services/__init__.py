from collections import defaultdict
from django.db import transaction, connection
from django.core.exceptions import ValidationError
from ardur.apps.usuarios.permissions import exigir_rol
from ardur.apps.financiera.models import CarteraDetalle
from ardur.apps.financiera.services import data_staging
from ardur.apps.expedientes.models import Expediente
from ardur.apps.preliminares.models import Preliminar
from ardur.apps.procesos.services import HistoricoMatcher, fingerprint
from ardur.apps.auditoria.services import registrar
from ardur.apps.ordenes.models import Orden
from .numbering import numero_oficial

def candidatos(importacion):
    return CarteraDetalle.objects.filter(importacion=importacion, importacion__aprobada=True, expediente__isnull=True, staging__requiere_revision=False, predio__isnull=False).exclude(staging__estado_historico__in=['PROCESO_ACTIVO', 'AMBIGUO', 'REQUIERE_REVISION']).select_related('predio', 'cliente', 'staging')

def grupos(importacion):
    grouped = defaultdict(list)
    for detail in candidatos(importacion):
        p = detail.predio
        grouped[(p.parroquia, p.zona, p.sector)].append(detail)
    return grouped

@transaction.atomic
def generar(importacion, territorios, usuario, numero_negocio=None):
    exigir_rol(usuario, 'JEFE_FINANCIERA')
    # Serializa la comprobación del histórico y creación en el límite de dominio.
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_advisory_xact_lock(81001)')
    selected = set(territorios)
    grouped = grupos(importacion)
    if not selected or not selected.issubset(grouped):
        raise ValidationError('Seleccione grupos vigentes de la vista preliminar.')
    orders = []
    history = HistoricoMatcher(Expediente.objects.select_related('cliente', 'detalle'))
    for territory in sorted(selected):
        order = Orden.objects.create(parroquia=territory[0], zona=territory[1], sector=territory[2], creado_por=usuario, numero_negocio=numero_oficial(numero_negocio))
        for detail in grouped[territory]:
            historic, match = history.match(data_staging(detail.staging), detail.predio)
            if historic in ('PROCESO_ACTIVO', 'AMBIGUO', 'REQUIERE_REVISION'):
                raise ValidationError(f'Caso {detail.ciu}: {historic}. No se generó ninguna orden; revise el histórico.')
            if historic in ('PROCESO_CERRADO', 'POSIBLE_NUEVA_DEUDA') and detail.staging.decision != 'ACEPTAR':
                raise ValidationError('Proceso cerrado/nueva deuda requiere decisión manual explícita.')
            identity = fingerprint({'predio': detail.predio, 'clave': detail.clave, 'ciu': detail.ciu, 'suministro': detail.suministro})
            if Expediente.objects.filter(caso_fingerprint=identity).exclude(estado='CERRADO').exists():
                raise ValidationError('Ya existe un expediente activo para este caso.')
            e = Expediente.objects.create(orden=order, cliente=detail.cliente, predio=detail.predio, detalle=detail, ciu=detail.ciu, suministro=detail.suministro, clave=detail.clave, caso_fingerprint=identity)
            history.add(e)
            Preliminar.objects.create(expediente=e)
            registrar(usuario, 'CREACION_EXPEDIENTE', e, {'orden': str(order.pk)})
        registrar(usuario, 'CREACION_ORDEN', order, {'expedientes': len(grouped[territory])})
        orders.append(order)
    return orders
