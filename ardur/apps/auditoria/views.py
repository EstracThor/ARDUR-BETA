from django.shortcuts import render
from django.core.paginator import Paginator
from ardur.apps.usuarios.permissions import roles_requeridos, tiene_rol
from .models import EventoAuditoria

@roles_requeridos('JEFE_FINANCIERA', 'JEFE_NOTIFICACIONES', 'CONSULTA')
def historial(request):
    qs = EventoAuditoria.objects.select_related('usuario')
    if not tiene_rol(request.user, 'JEFE_FINANCIERA'):
        qs = qs.filter(accion__in=['CREACION_LOTE', 'ASIGNACION_NOTIFICADOR', 'RESULTADO_NOTIFICACION'])
    if request.GET.get('entidad'):
        qs = qs.filter(id_entidad=request.GET['entidad'])
    return render(request, 'auditoria/historial.html', {'title': 'Historial de auditoría', 'page': Paginator(qs, 50).get_page(request.GET.get('page'))})
