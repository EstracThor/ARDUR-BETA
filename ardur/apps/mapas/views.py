from django.shortcuts import render, get_object_or_404
from django.conf import settings
from ardur.apps.usuarios.permissions import roles_requeridos, tiene_rol
from ardur.apps.notificaciones.selectors import ordenes_visibles, expedientes_visibles
from ardur.apps.notificaciones.views import lotes_visibles
from .services import extension
from ardur.apps.core.validators import uuid_o_404

@roles_requeridos('JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
def mapa(request):
    orders = ordenes_visibles(request.user).order_by('-fecha_creacion')
    order = get_object_or_404(orders, pk=uuid_o_404(request.GET['orden'])) if request.GET.get('orden') else None
    lote = None
    if request.GET.get('lote'):
        lote = get_object_or_404(lotes_visibles(request.user), pk=uuid_o_404(request.GET['lote']), orden=order)
    qs = expedientes_visibles(request.user).filter(orden=order)
    if lote:
        qs = qs.filter(asignacion__lote=lote)
    printing = request.GET.get('imprimir') == '1'
    return render(request, 'mapas/mapa.html', {'title': 'Mapa de notificaciones', 'ordenes': orders, 'orden': order, 'lote': lote, 'bbox': extension(request.user, order, lote) if order else None, 'total': qs.count(), 'sin_geometria': qs.filter(predio__isnull=True).count(), 'imprimir': printing, 'tile_url': settings.MAP_TILE_URL, 'tile_attribution': settings.MAP_TILE_ATTRIBUTION})

@roles_requeridos('JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
def listado_imprimible(request, pk):
    lot = get_object_or_404(lotes_visibles(request.user), pk=pk)
    rows = lot.asignaciones.select_related('expediente__cliente', 'expediente__predio', 'usuario_notificador').order_by('fecha_creacion')
    if not tiene_rol(request.user, 'JEFE_NOTIFICACIONES', 'CONSULTA'):
        rows = rows.filter(usuario_notificador=request.user)
    return render(request, 'notificaciones/imprimir.html', {'title': 'Listado de trabajo', 'lote': lot, 'asignaciones': rows, 'imprimir': True})
