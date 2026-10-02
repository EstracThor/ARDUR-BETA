import logging
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import connection
from ardur.apps.usuarios.permissions import tiene_rol

@login_required
def home(request):
    if tiene_rol(request.user, 'JEFE_FINANCIERA'):
        return redirect('fin-dashboard')
    return redirect('notif-dashboard')

def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        logging.getLogger(__name__).exception('Healthcheck: base de datos no disponible')
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})
