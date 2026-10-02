from django.http import FileResponse
from django.shortcuts import get_object_or_404
from ardur.apps.usuarios.permissions import roles_requeridos, tiene_rol
from ardur.apps.financiera.models import ImportacionCartera
from ardur.apps.preliminares.models import Preliminar
from ardur.apps.notificaciones.selectors import expedientes_visibles

@roles_requeridos('JEFE_FINANCIERA')
def cartera_original(request, pk):
    imp = get_object_or_404(ImportacionCartera, pk=pk)
    return FileResponse(imp.archivo_original.open('rb'), as_attachment=True)

@roles_requeridos('JEFE_FINANCIERA', 'JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
def preliminar_pdf(request, pk):
    qs = Preliminar.objects.exclude(archivo_pdf='')
    if not tiene_rol(request.user, 'JEFE_FINANCIERA'):
        qs = qs.filter(expediente__in=expedientes_visibles(request.user))
    p = get_object_or_404(qs, pk=pk)
    return FileResponse(p.archivo_pdf.open('rb'), as_attachment=True, content_type='application/pdf')
