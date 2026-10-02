from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.http import JsonResponse
from django.urls import reverse
from ardur.apps.usuarios.permissions import roles_requeridos
from ardur.apps.catastro.models import Predio
from .models import ImportacionCartera, RegistroCarteraStaging
from .forms import ImportacionForm, RevisionForm
from .selectors import staging_filtrado, FILTROS
from .services import subir, revisar, aprobar, enviar_tarea

@roles_requeridos('JEFE_FINANCIERA')
def dashboard(request):
    imp = ImportacionCartera.objects.order_by('-fecha_creacion').first()
    rows = RegistroCarteraStaging.objects.filter(raw__importacion=imp)
    stats = rows.aggregate(total=Count('id'), nuevos=Count('id', filter=Q(estado_historico='NUEVO')), activos=Count('id', filter=Q(estado_historico='PROCESO_ACTIVO')), cerrados=Count('id', filter=Q(estado_historico='PROCESO_CERRADO')), revision=Count('id', filter=Q(requiere_revision=True)), sin_catastro=Count('id', filter=Q(estado_catastro='SIN_COINCIDENCIA')), fallecidos=Count('id', filter=Q(fallecido=True)), errores=Count('id', filter=Q(estado_validacion='ERROR')))
    labels = {'total': 'Total registros', 'nuevos': 'Nuevos', 'activos': 'Proceso activo', 'cerrados': 'Proceso cerrado', 'revision': 'Revisión', 'sin_catastro': 'Sin catastro', 'fallecidos': 'Fallecidos', 'errores': 'Errores'}
    return render(request, 'financiera/dashboard.html', {'title': 'Dashboard financiera', 'importacion': imp, 'stats': {labels[key]: value for key, value in stats.items()}})

@roles_requeridos('JEFE_FINANCIERA')
def importaciones(request):
    page = Paginator(ImportacionCartera.objects.select_related('usuario').order_by('-fecha_creacion'), 25).get_page(request.GET.get('page'))
    return render(request, 'financiera/importaciones.html', {'title': 'Carteras e histórico mensual', 'page': page})

@roles_requeridos('JEFE_FINANCIERA')
def ultima_depuracion(request, excepciones=False):
    imp = ImportacionCartera.objects.order_by('-fecha_creacion').first()
    if not imp:
        messages.info(request, 'Importe una cartera para comenzar la depuración.')
        return redirect('fin-nueva')
    url = reverse('fin-depuracion', kwargs={'pk': imp.pk})
    return redirect(url + ('?filtro=revision' if excepciones else ''))

@roles_requeridos('JEFE_FINANCIERA')
def nueva(request):
    form = ImportacionForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            imp = subir(form.cleaned_data['archivo'], form.cleaned_data['periodo'], form.cleaned_data['hoja'], request.user)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Archivo conservado. Puede consultar el estado de procesamiento.')
            return redirect('fin-depuracion', pk=imp.pk)
    return render(request, 'form.html', {'title': 'Nueva importación', 'form': form, 'submit': 'Subir y procesar', 'help': 'Seleccione la hoja original de cartera. El SHA-256 impide subir el mismo archivo dos veces.'})

@roles_requeridos('JEFE_FINANCIERA')
def depuracion(request, pk):
    imp = get_object_or_404(ImportacionCartera, pk=pk)
    filtro, buscar = request.GET.get('filtro', 'todos'), request.GET.get('q', '')
    page = Paginator(staging_filtrado(imp, filtro, buscar), 50).get_page(request.GET.get('page'))
    return render(request, 'financiera/depuracion.html', {'title': 'Depuración de cartera', 'importacion': imp, 'page': page, 'filtros': FILTROS, 'filtro': filtro, 'buscar': buscar})

@roles_requeridos('JEFE_FINANCIERA')
def estado(request, pk):
    imp = get_object_or_404(ImportacionCartera, pk=pk)
    return JsonResponse({key: getattr(imp, key) for key in ('estado', 'total_filas', 'filas_validas', 'filas_revision', 'filas_error', 'error')})

@require_POST
@roles_requeridos('JEFE_FINANCIERA')
def reintentar(request, pk):
    imp = get_object_or_404(ImportacionCartera, pk=pk)
    if imp.estado != 'ERROR' or imp.aprobada:
        messages.error(request, 'Solo se reintentan importaciones con ERROR, no aprobadas.')
    else:
        ImportacionCartera.objects.filter(pk=imp.pk).update(estado='PENDIENTE', error='')
        enviar_tarea(imp)
        messages.info(request, 'Reintento solicitado. El archivo original y RAW se conservan.')
    return redirect('fin-depuracion', pk=pk)

@roles_requeridos('JEFE_FINANCIERA')
def revision(request, pk):
    s = get_object_or_404(RegistroCarteraStaging.objects.select_related('raw__importacion', 'predio'), pk=pk)
    form = RevisionForm(request.POST or None, instance=s, initial={'predio_id_manual': s.predio_id})
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        predio = Predio.objects.filter(pk=d['predio_id_manual']).first() if d.get('predio_id_manual') else None
        try:
            revisar(pk, request.user, {key: d[key] for key in form.Meta.fields}, predio, d['decision'], d['motivo'])
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Decisión registrada en auditoría; RAW conservado.')
            return redirect('fin-depuracion', pk=s.raw.importacion_id)
    cat = Predio.objects.filter(version=s.raw.importacion.catastro_version).defer('geom')
    query = request.GET.get('predio_q', '')
    if query:
        cat = cat.filter(Q(clave_ante__icontains=query) | Q(clave_nuev__icontains=query) | Q(clave_ag__icontains=query) | Q(cod_client__icontains=query) | Q(predio_mun__icontains=query))
    else:
        cat = cat.filter(pk__in=s.candidatos_catastro)
    return render(request, 'financiera/revision.html', {'title': 'Revisión individual', 'registro': s, 'form': form, 'predios': cat[:30], 'predio_q': query})

@require_POST
@roles_requeridos('JEFE_FINANCIERA')
def aprobar_view(request, pk):
    try:
        count = aprobar(pk, request.user)
        messages.success(request, f'Depuración aprobada: {count} snapshots. Las excepciones se conservaron.')
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    return redirect('fin-depuracion', pk=pk)
