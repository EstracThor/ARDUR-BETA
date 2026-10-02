import re
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError

HEADERS = ('CIU', 'CEDULA_RUC', 'NOMBRES', 'CLAVE', 'DIRECCION', 'PARROQUIA', 'TELEF', 'CORREO', 'TOTAL_EMISION', 'TOTAL_INTERES', 'TOTAL_COACTIVA', 'TOTAL_RECARGO', 'MESES_DEUDA')
MONEY = ('total_emision', 'total_interes', 'total_coactiva', 'total_recargo')

def texto(value):
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()

def identificador(value):
    return re.sub(r'\s+', '', texto(value)).upper()

def fallecido(nombre):
    return '+' in str(nombre or '')

def dinero(value):
    if value in (None, ''):
        return Decimal('0.00')
    try:
        amount = Decimal(texto(value))
    except InvalidOperation as exc:
        raise ValidationError('Valor monetario no numérico; revise el formato.') from exc
    if not amount.is_finite() or amount < 0 or amount >= Decimal('10000000000000000'):
        raise ValidationError('Valor monetario fuera de rango.')
    if amount != amount.quantize(Decimal('0.01')):
        raise ValidationError('Valor monetario tiene más de dos decimales.')
    return amount.quantize(Decimal('0.01'))

def normalizar(row):
    data = {k.lower(): texto(row.get(k)) for k in HEADERS if not k.startswith('TOTAL_') and k != 'MESES_DEUDA'}
    data['telefono'] = data.pop('telef')
    for key in ('ciu', 'cedula_ruc', 'clave'):
        data[key] = identificador(row.get(key.upper()))
    for key in MONEY:
        data[key] = dinero(row.get(key.upper()))
    months = dinero(row.get('MESES_DEUDA'))
    if months != months.to_integral_value() or months > 2147483647:
        raise ValidationError('MESES_DEUDA debe ser un entero no negativo.')
    data['meses_deuda'] = int(months)
    data['fallecido'] = fallecido(data['nombres'])
    if not data['nombres'] or not (data['clave'] or data['ciu']):
        raise ValidationError('Se requieren nombres y un identificador de caso (CLAVE o CIU).')
    return data
