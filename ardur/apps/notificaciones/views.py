from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from ardur.apps.usuarios.permissions import roles_requeridos, tiene_rol
from .selectors import expedientes_visibles, ordenes_visibles
from .models import LoteNotificacion, AsignacionNotificador
from .forms import LoteForm, ResultadoForm
from .services import crear_lote, registrar_resultado

@roles_requeridos('JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
def dashboard(request):
    cases = expedientes_visibles(request.user)
    lots = lotes_visibles(request.user)
    stats = {'ordenes': ordenes_visibles(request.user).count(), 'listos': cases.filter(estado='LISTO_PARA_NOTIFICAR').count(), 'sectores': cases.values('orden__parroquia', 'orden__zona', 'orden__sector').distinct().count(), 'lotes_pendientes': lots.exclude(estado='COMPLETADO').count(), 'asignados': cases.filter(estado='ASIGNADO_NOTIFICACION').count(), 'notificados': cases.filter(estado='NOTIFICADO').count()}
    labels = {'ordenes': 'Órdenes transferidas', 'listos': 'Expedientes listos', 'sectores': 'Territorios', 'lotes_pendientes': 'Lotes pendientes', 'asignados': 'Asignaciones pendientes', 'notificados': 'Notificados'}
    return render(request, 'notificaciones/dashboard.html', {'title': 'Dashboard notificaciones', 'stats': {labels[key]: value for key, value in stats.items()}})

def lotes_visibles(user):
    qs = LoteNotificacion.objects.select_related('orden', 'responsable')
    if tiene_rol(user, 'JEFE_NOTIFICACIONES', 'CONSULTA'):
        return qs
    return qs.filter(asignaciones__usuario_notificador=user).distinct()

@roles_requeridos('JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
def ordenes(request):
    qs = ordenes_visibles(request.user).order_by('-fecha_creacion')
    for field in ('parroquia', 'zona', 'sector'):
        if request.GET.get(field):
            qs = qs.filter(**{field: request.GET[field]})
    return render(request, 'notificaciones/ordenes.html', {'title': 'Órdenes transferidas', 'page': Paginator(qs, 25).get_page(request.GET.get('page'))})

@roles_requeridos('JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
def orden(request, pk):
    order = get_object_or_404(ordenes_visibles(request.user), pk=pk)
    cases = expedientes_visibles(request.user).filter(orden=order).order_by('fecha_creacion')
    return render(request, 'notificaciones/orden.html', {'title': 'Expedientes de la orden', 'orden': order, 'page': Paginator(cases, 50).get_page(request.GET.get('page'))})

@roles_requeridos('JEFE_NOTIFICACIONES')
def nuevo_lote(request, pk):
    order = get_object_or_404(ordenes_visibles(request.user), pk=pk)
    form = LoteForm(request.POST or None, orden=order)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        try:
            lote = crear_lote(order, d['fecha_programada'], d['notificador'], [e.pk for e in d['expedientes']], request.user)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Lote creado y expedientes asignados.')
            return redirect('notif-lote', pk=lote.pk)
    return render(request, 'form.html', {'title': 'Crear lote y asignar', 'form': form, 'submit': 'Crear lote', 'help': str(order)})

@roles_requeridos('JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
def lotes(request):
    return render(request, 'notificaciones/lotes.html', {'title': 'Lotes de notificación', 'page': Paginator(lotes_visibles(request.user).order_by('-fecha_creacion'), 25).get_page(request.GET.get('page'))})

@roles_requeridos('JEFE_NOTIFICACIONES', 'NOTIFICADOR', 'CONSULTA')
def lote(request, pk):
    lot = get_object_or_404(lotes_visibles(request.user), pk=pk)
    rows = lot.asignaciones.select_related('expediente__cliente', 'expediente__predio', 'usuario_notificador')
    if not tiene_rol(request.user, 'JEFE_NOTIFICACIONES', 'CONSULTA'):
        rows = rows.filter(usuario_notificador=request.user)
    return render(request, 'notificaciones/lote.html', {'title': 'Listado de trabajo', 'lote': lot, 'page': Paginator(rows.order_by('fecha_creacion'), 50).get_page(request.GET.get('page'))})

@roles_requeridos('JEFE_NOTIFICACIONES')
def resultado(request, pk):
    a = get_object_or_404(AsignacionNotificador.objects.select_related('expediente', 'lote'), pk=pk)
    form = ResultadoForm(request.POST or None, initial={'observaciones': a.observaciones})
    if request.method == 'POST' and form.is_valid():
        try:
            registrar_resultado(pk, form.cleaned_data['estado'], form.cleaned_data['observaciones'], request.user)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Resultado registrado.')
            return redirect('notif-lote', pk=a.lote_id)
    return render(request, 'form.html', {'title': 'Registrar resultado', 'form': form, 'submit': 'Guardar resultado', 'help': str(a.expediente)})

@roles_requeridos('JEFE_NOTIFICACIONES', 'CONSULTA')
def notificadores(request):
    from django.db.models import Count
    users = get_user_model().objects.filter(groups__name='NOTIFICADOR').annotate(asignaciones=Count('asignacionnotificador')).order_by('username')
    return render(request, 'notificaciones/notificadores.html', {'title': 'Notificadores', 'notificadores': users})
