import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.http import require_POST
from ardur.apps.usuarios.permissions import roles_requeridos
from ardur.apps.financiera.models import ImportacionCartera
from ardur.apps.auditoria.services import registrar
from .models import Orden
from .services import grupos, generar

@roles_requeridos('JEFE_FINANCIERA')
def listado(request):
    from django.db.models import Count
    page = Paginator(Orden.objects.annotate(cantidad=Count('expedientes')).order_by('-fecha_creacion'), 25).get_page(request.GET.get('page'))
    return render(request, 'ordenes/listado.html', {'title': 'Órdenes', 'page': page})

@roles_requeridos('JEFE_FINANCIERA')
def preview(request, pk):
    imp = get_object_or_404(ImportacionCartera, pk=pk, aprobada=True)
    if request.method == 'POST':
        try:
            territories = [tuple(json.loads(v)) for v in request.POST.getlist('territorios')]
            if any(len(t) != 3 or not all(isinstance(i, str) for i in t) for t in territories):
                raise ValueError('Territorio inválido.')
            orders = generar(imp, territories, request.user)
        except (ValidationError, ValueError, TypeError) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f'{len(orders)} órdenes creadas con sus expedientes.')
            return redirect('fin-ordenes')
    groups = [{'parroquia': t[0], 'zona': t[1], 'sector': t[2], 'cantidad': len(rows), 'key': json.dumps(t)} for t, rows in grupos(imp).items()]
    return render(request, 'ordenes/preview.html', {'title': 'Vista preliminar territorial', 'grupos': groups, 'importacion': imp})

@roles_requeridos('JEFE_FINANCIERA')
def detalle(request, pk):
    order = get_object_or_404(Orden, pk=pk)
    page = Paginator(order.expedientes.select_related('cliente', 'predio').order_by('fecha_creacion'), 50).get_page(request.GET.get('page'))
    return render(request, 'ordenes/detalle.html', {'title': 'Orden y expedientes', 'orden': order, 'page': page})

@require_POST
@roles_requeridos('JEFE_FINANCIERA')
def numero(request, pk):
    from .services.numbering import numero_oficial
    with transaction.atomic():
        order = get_object_or_404(Orden.objects.select_for_update(), pk=pk)
        value = request.POST.get('numero_negocio', '')
        if len(value) > 100:
            messages.error(request, 'Máximo 100 caracteres.')
        else:
            before = order.numero_negocio
            order.numero_negocio = numero_oficial(value)
            order.save(update_fields=['numero_negocio'])
            registrar(request.user, 'NUMERO_ORDEN', order, antes={'numero': before}, despues={'numero': order.numero_negocio})
    return redirect('fin-orden', pk=pk)
