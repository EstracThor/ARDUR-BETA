from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

FINANCIERA = 'JEFE_FINANCIERA'
NOTIFICACIONES = 'JEFE_NOTIFICACIONES'

def tiene_rol(usuario, *roles):
    return usuario.is_authenticated and (usuario.is_superuser or usuario.groups.filter(name__in=('ADMINISTRADOR', *roles)).exists())

def exigir_rol(usuario, *roles):
    if not tiene_rol(usuario, *roles):
        raise PermissionDenied('Su rol no permite esta operación.')

def roles_requeridos(*roles):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            exigir_rol(request.user, *roles)
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
