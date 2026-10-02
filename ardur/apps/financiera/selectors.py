from django.db.models import Q
from .models import RegistroCarteraStaging

FILTROS = [('todos', 'Todos'), ('nuevo', 'Nuevos'), ('activo', 'Proceso activo'), ('cerrado', 'Proceso cerrado'), ('nueva_deuda', 'Nueva deuda'), ('fallecidos', 'Fallecidos'), ('sin_catastro', 'Sin catastro'), ('ambiguos', 'Ambiguos'), ('revision', 'Revisión'), ('errores', 'Errores')]

def staging_filtrado(importacion, filtro='todos', buscar=''):
    qs = RegistroCarteraStaging.objects.filter(raw__importacion=importacion).select_related('predio', 'raw').order_by('raw__numero_fila')
    filters = {'nuevo': Q(estado_historico='NUEVO'), 'activo': Q(estado_historico='PROCESO_ACTIVO'), 'cerrado': Q(estado_historico='PROCESO_CERRADO'), 'nueva_deuda': Q(estado_historico='POSIBLE_NUEVA_DEUDA'), 'fallecidos': Q(fallecido=True), 'sin_catastro': Q(estado_catastro='SIN_COINCIDENCIA'), 'ambiguos': Q(estado_historico='AMBIGUO') | Q(estado_catastro__in=['AMBIGUO', 'CONFLICTO_IDENTIDAD']), 'revision': Q(requiere_revision=True), 'errores': Q(estado_validacion='ERROR')}
    if filtro in filters:
        qs = qs.filter(filters[filtro])
    if buscar:
        qs = qs.filter(Q(ciu__icontains=buscar) | Q(cedula_ruc__icontains=buscar) | Q(nombres__icontains=buscar) | Q(clave__icontains=buscar))
    return qs
