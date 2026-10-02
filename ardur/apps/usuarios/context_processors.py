from .permissions import tiene_rol

def roles(request):
    return {'es_financiera': tiene_rol(request.user, 'JEFE_FINANCIERA'), 'es_notificaciones': tiene_rol(request.user, 'JEFE_NOTIFICACIONES'), 'es_notificador': tiene_rol(request.user, 'NOTIFICADOR'), 'es_consulta': tiene_rol(request.user, 'CONSULTA')}
