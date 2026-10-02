import hashlib
from collections import defaultdict
from ardur.apps.financiera.normalization import identificador

KEY_FIELDS = ('clave_ante', 'clave_nuev', 'clave_ag', 'predio_mun')

def claves_caso(data):
    clave = identificador(data.get('clave', ''))
    # La CLAVE compuesta se usa solo para buscar candidatos; conflictos pasan a revisión.
    return list(dict.fromkeys(v for v in (clave, clave.split('/')[0]) if v))

def fingerprint(data):
    # No depende de la cédula. Se revalida con todo el histórico antes de crear.
    identity = str(data['predio'].pk) if data.get('predio') else '|'.join([identificador(data.get('clave')), identificador(data.get('ciu')), identificador(data.get('suministro'))])
    return hashlib.sha256(identity.encode()).hexdigest()

class CatastroMatcher:
    def __init__(self, predios):
        self.predios = {}
        self.keys = defaultdict(set)
        self.clients = defaultdict(set)
        self.supplies = defaultdict(set)
        for p in predios:
            self.predios[str(p.pk)] = p
            for field in KEY_FIELDS:
                if value := identificador(getattr(p, field)):
                    self.keys[value].add(str(p.pk))
            if value := identificador(p.cod_client):
                self.clients[value.lstrip('0') or '0'].add(str(p.pk))
            if value := identificador(p.suministro):
                self.supplies[value].add(str(p.pk))

    def match(self, data):
        sets = []
        keys = set().union(*(self.keys.get(k, set()) for k in claves_caso(data)))
        if keys:
            sets.append(keys)
        ciu = identificador(data.get('ciu')).lstrip('0') or '0'
        if candidates := self.clients.get(ciu):
            sets.append(candidates)
        if candidates := self.supplies.get(identificador(data.get('suministro'))):
            sets.append(candidates)
        if not sets:
            return None, [], 'SIN_COINCIDENCIA'
        # Ningún identificador conocido puede contradecir al seleccionado.
        union = set.union(*sets)
        if len(union) != 1:
            return None, sorted(union), 'AMBIGUO'
        p = self.predios[next(iter(union))]
        if not p.geometria_valida:
            return None, [str(p.pk)], 'GEOMETRIA_INVALIDA'
        cedula = identificador(data.get('cedula_ruc'))
        cat_cedula = identificador(p.ruc_cedula_catastro)
        if cedula and cat_cedula and cedula != cat_cedula:
            return None, [str(p.pk)], 'CONFLICTO_IDENTIDAD'
        return p, [str(p.pk)], 'COINCIDENCIA'

class HistoricoMatcher:
    def __init__(self, expedientes):
        self.items = {}
        self.index = defaultdict(set)
        self.cedulas = defaultdict(set)
        for e in expedientes:
            self.add(e)

    def add(self, e):
        key = str(e.pk)
        self.items[key] = e
        for name, value in (('predio', str(e.predio_id or '')), ('ciu', identificador(e.ciu).lstrip('0')), ('suministro', identificador(e.suministro)), *[('clave', k) for k in claves_caso({'clave': e.clave})]):
            if value:
                self.index[(name, value)].add(key)
        if e.cliente.cedula_ruc_normalizada:
            self.cedulas[e.cliente.cedula_ruc_normalizada].add(key)

    def match(self, data, predio=None):
        candidates = set()
        for name, value in (('predio', str(predio.pk) if predio else ''), ('ciu', identificador(data.get('ciu')).lstrip('0')), ('suministro', identificador(data.get('suministro'))), *[('clave', k) for k in claves_caso(data)]):
            if value:
                candidates.update(self.index.get((name, value), set()))
        if len(candidates) > 1:
            return 'AMBIGUO', None
        if not candidates:
            if self.cedulas.get(data.get('cedula_ruc')) and predio is None:
                return 'REQUIERE_REVISION', None
            return 'NUEVO', None
        e = self.items[next(iter(candidates))]
        if data.get('cedula_ruc') and e.cliente.cedula_ruc_normalizada and data['cedula_ruc'] != e.cliente.cedula_ruc_normalizada:
            return 'AMBIGUO', e
        if e.estado != 'CERRADO':
            return 'PROCESO_ACTIVO', e
        old_amount = e.detalle.total_emision + e.detalle.total_interes + e.detalle.total_coactiva + e.detalle.total_recargo
        amount = sum(data.get(k, 0) for k in ('total_emision', 'total_interes', 'total_coactiva', 'total_recargo'))
        return ('POSIBLE_NUEVA_DEUDA' if amount > old_amount else 'PROCESO_CERRADO'), e
