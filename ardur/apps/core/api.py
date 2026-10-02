from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from ardur.apps.usuarios.permissions import tiene_rol, exigir_rol
from ardur.apps.notificaciones.selectors import expedientes_visibles, ordenes_visibles
from ardur.apps.notificaciones.views import lotes_visibles
from ardur.apps.ordenes.models import Orden
from ardur.apps.expedientes.models import Expediente
from ardur.apps.mapas.services import geojson
from .validators import uuid_o_404

def paginado(request, queryset):
    pagination = PageNumberPagination()
    pagination.page_size = 50
    result = pagination.paginate_queryset(queryset, request)
    return pagination.get_paginated_response(list(result))

@api_view(['GET'])
def health(request):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('SELECT PostGIS_Version()')
        version = cursor.fetchone()[0]
    return Response({'status': 'ok', 'postgis': version})

@api_view(['GET'])
def ordenes(request):
    exigir_rol(request.user, 'JEFE_FINANCIERA', 'JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
    qs = Orden.objects.all() if tiene_rol(request.user, 'JEFE_FINANCIERA') else ordenes_visibles(request.user)
    return paginado(request, qs.order_by('-fecha_creacion').values('id', 'numero_negocio', 'parroquia', 'zona', 'sector', 'estado'))

@api_view(['GET'])
def expedientes(request):
    exigir_rol(request.user, 'JEFE_FINANCIERA', 'JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
    qs = Expediente.objects.all() if tiene_rol(request.user, 'JEFE_FINANCIERA') else expedientes_visibles(request.user)
    if request.GET.get('orden'):
        qs = qs.filter(orden_id=uuid_o_404(request.GET['orden']))
    return paginado(request, qs.order_by('-fecha_creacion').values('id', 'orden_id', 'numero_negocio', 'estado'))

@api_view(['GET'])
def lotes(request):
    exigir_rol(request.user, 'JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
    return paginado(request, lotes_visibles(request.user).order_by('-fecha_creacion').values('id', 'orden_id', 'fecha_programada', 'estado'))

@api_view(['GET'])
def mapa_geojson(request):
    exigir_rol(request.user, 'JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
    if not request.GET.get('orden'):
        return Response({'detail': 'Se requiere una orden.'}, status=400)
    order = get_object_or_404(ordenes_visibles(request.user), pk=uuid_o_404(request.GET['orden']))
    lote = get_object_or_404(lotes_visibles(request.user), pk=uuid_o_404(request.GET['lote']), orden=order) if request.GET.get('lote') else None
    try:
        return Response(geojson(request.user, order, request.GET.get('bbox'), lote, request.GET))
    except ValidationError as exc:
        return Response({'detail': '; '.join(exc.messages)}, status=400)
