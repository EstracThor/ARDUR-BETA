from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from ardur.apps.usuarios.permissions import roles_requeridos
from ardur.apps.preliminares.forms import PreliminarForm
from ardur.apps.preliminares.services import registrar_preliminar, transferir
from .models import Expediente
from .services import actualizar_numero, cerrar

@roles_requeridos('JEFE_FINANCIERA')
def listado(request):
    qs = Expediente.objects.select_related('cliente', 'orden').order_by('-fecha_creacion')
    if request.GET.get('estado'):
        qs = qs.filter(estado=request.GET['estado'])
    return render(request, 'expedientes/listado.html', {'title': 'Expedientes e histórico de procesos', 'page': Paginator(qs, 50).get_page(request.GET.get('page'))})

@roles_requeridos('JEFE_FINANCIERA')
def detalle(request, pk):
    e = get_object_or_404(Expediente.objects.select_related('orden', 'cliente', 'predio', 'detalle', 'preliminar'), pk=pk)
    form = PreliminarForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        try:
            registrar_preliminar(pk, request.user, d['archivo_pdf'], d['cantidad_titulos'], d['recargo_reportado'])
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Preliminar externa registrada. Ya puede transferir el expediente.')
            return redirect('fin-expediente', pk=pk)
    return render(request, 'expedientes/detalle.html', {'title': 'Expediente', 'expediente': e, 'form': form})

@require_POST
@roles_requeridos('JEFE_FINANCIERA')
def transferir_view(request, pk):
    try:
        transferir(pk, request.user)
        messages.success(request, 'Expediente listo para Notificaciones.')
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    return redirect('fin-expediente', pk=pk)

@require_POST
@roles_requeridos('JEFE_FINANCIERA')
def numero(request, pk):
    value = request.POST.get('numero_negocio', '')
    if len(value) <= 100:
        actualizar_numero(pk, value, request.user)
        messages.success(request, 'Número actualizado.')
    else:
        messages.error(request, 'Máximo 100 caracteres.')
    return redirect('fin-expediente', pk=pk)

@require_POST
@roles_requeridos('JEFE_FINANCIERA')
def cerrar_view(request, pk):
    try:
        cerrar(pk, request.POST.get('motivo', ''), request.user)
        messages.success(request, 'Proceso cerrado y auditado.')
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    return redirect('fin-expediente', pk=pk)
