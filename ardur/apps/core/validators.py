from uuid import UUID
from django.http import Http404

def uuid_o_404(value):
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise Http404('Identificador inválido.') from exc
