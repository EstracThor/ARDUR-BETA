import json
import tempfile
from pathlib import Path
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from ardur.apps.usuarios.permissions import exigir_rol
from ardur.apps.documentos.services import sha256, validar_archivo
from ardur.apps.auditoria.services import registrar
from ardur.apps.catastro.models import CatastroVersion, Predio
from ardur.apps.clientes.models import Cliente
from ardur.apps.expedientes.models import Expediente
from ardur.apps.procesos.services import CatastroMatcher, HistoricoMatcher
from .models import ImportacionCartera, RegistroCarteraRaw, RegistroCarteraStaging, CarteraDetalle
from .normalization import normalizar, MONEY, fallecido, identificador, dinero
from .readers import filas_excel

def subir(archivo, periodo, hoja, usuario):
    exigir_rol(usuario, 'JEFE_FINANCIERA')
    validar_archivo(archivo, {'.xls', '.xlsx'})
    digest = sha256(archivo)
    with transaction.atomic():
        # get_or_create maneja la carrera respaldada por la restricción SHA única.
        imp, created = ImportacionCartera.objects.get_or_create(sha256=digest, defaults={'periodo': periodo, 'hoja': hoja, 'usuario': usuario})
        if not created:
            raise ValidationError('Este archivo ya fue importado; consulte la importación existente.')
        imp.archivo_original.save(Path(archivo.name).name, archivo, save=True)
        registrar(usuario, 'IMPORTACION_SUBIDA', imp, {'sha256': digest, 'hoja': hoja})
        transaction.on_commit(lambda: enviar_tarea(imp))
    # La tarea se solicita tras confirmar DB. Un fallo del broker queda visible y reintentable.
    return imp

def enviar_tarea(imp):
    from .tasks import procesar_importacion
    try:
        result = procesar_importacion.delay(str(imp.pk))
        ImportacionCartera.objects.filter(pk=imp.pk).update(task_id=result.id, error='')
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception('No se pudo publicar la tarea')
        ImportacionCartera.objects.filter(pk=imp.pk).update(estado='ERROR', error=f'No se pudo enviar al worker: {type(exc).__name__}: {exc}'[:4000])

def procesar(importacion_id):
    with transaction.atomic():
        imp = ImportacionCartera.objects.select_for_update().get(pk=importacion_id)
        if imp.estado not in ('PENDIENTE', 'ERROR') or imp.aprobada:
            return imp.estado
        imp.estado = 'PROCESANDO'
        imp.error = ''
        imp.catastro_version = CatastroVersion.objects.filter(activo=True).first()
        imp.save()
    catastro = CatastroMatcher(Predio.objects.filter(version=imp.catastro_version).defer('geom').iterator(chunk_size=2000))
    history = HistoricoMatcher(Expediente.objects.select_related('cliente', 'detalle').iterator(chunk_size=2000))
    seen = set()
    previous_raw = {r.numero_fila: r for r in imp.raw.all()}
    previous_staging = set(RegistroCarteraStaging.objects.filter(raw__importacion=imp).values_list('raw_id', flat=True))
    valid = review = errors = total = 0
    # FileField.open permite almacenamiento local o S3; los lectores requieren ruta temporal.
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / ('cartera' + Path(imp.archivo_original.name).suffix)
        with imp.archivo_original.open('rb') as source, path.open('wb') as target:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                target.write(chunk)
        with filas_excel(path, imp.hoja) as rows:
            raw_batch, staging_batch = [], []
            for number, original, source in rows:
                total += 1
                raw = RegistroCarteraRaw(importacion=imp, numero_fila=number, datos_originales=original)
                # Reintentar nunca borra RAW. Ya confirmado: se reutiliza sin modificar.
                existing = previous_raw.get(number)
                if existing:
                    raw = existing
                    if raw.pk in previous_staging:
                        seen.add(json.dumps(original, sort_keys=True, ensure_ascii=False))
                        continue
                else:
                    raw_batch.append(raw)
                staging = RegistroCarteraStaging(raw=raw)
                try:
                    data = normalizar(source)
                    for key, value in data.items():
                        setattr(staging, key, value)
                    signature = json.dumps(original, sort_keys=True, ensure_ascii=False)
                    p, candidates, status = catastro.match(data)
                    staging.predio = p
                    staging.candidatos_catastro = candidates
                    staging.estado_catastro = status
                    staging.fallecido = data['fallecido'] or (p is not None and fallecido(p.nombres_catastro))
                    historic, process = history.match(data, p)
                    staging.estado_historico = historic
                    staging.proceso_coincidente = process
                    reasons = []
                    if signature in seen:
                        staging.estado_validacion = 'REPETIDO'
                        reasons.append('Fila repetida exacta dentro del archivo; no se consolida automáticamente.')
                    seen.add(signature)
                    if status != 'COINCIDENCIA':
                        reasons.append('Catastro: ' + status)
                    if historic not in ('NUEVO', 'PROCESO_ACTIVO'):
                        reasons.append('Histórico: ' + historic)
                    staging.requiere_revision = bool(reasons)
                    staging.motivo_revision = ' | '.join(reasons)
                except ValidationError as exc:
                    staging.estado_validacion = 'ERROR'
                    staging.requiere_revision = True
                    staging.motivo_revision = '; '.join(exc.messages)
                staging_batch.append(staging)
                if len(staging_batch) >= 500:
                    guardar_batch(raw_batch, staging_batch)
                    raw_batch, staging_batch = [], []
                    ImportacionCartera.objects.filter(pk=imp.pk).update(total_filas=total)
            guardar_batch(raw_batch, staging_batch)
    qs = RegistroCarteraStaging.objects.filter(raw__importacion=imp)
    errors = qs.filter(estado_validacion='ERROR').count()
    review = qs.filter(requiere_revision=True).count()
    valid = qs.filter(requiere_revision=False).count()
    with transaction.atomic():
        imp.estado = 'COMPLETADO_CON_ADVERTENCIAS' if review else 'COMPLETADO'
        imp.total_filas, imp.filas_validas, imp.filas_revision, imp.filas_error = total, valid, review, errors
        imp.save()
        registrar(imp.usuario, 'IMPORTACION_PROCESADA', imp, {'total': total, 'validas': valid, 'revision': review, 'errores': errors})
    return imp.estado

def guardar_batch(raw, staging):
    if not staging:
        return
    with transaction.atomic():
        RegistroCarteraRaw.objects.bulk_create(raw)
        RegistroCarteraStaging.objects.bulk_create(staging)

def data_staging(s):
    return {key: getattr(s, key) for key in ('ciu', 'cedula_ruc', 'clave', 'suministro', *MONEY)}

@transaction.atomic
def revisar(staging_id, usuario, valores, predio, decision, motivo):
    exigir_rol(usuario, 'JEFE_FINANCIERA')
    reference = RegistroCarteraStaging.objects.only('raw_id').get(pk=staging_id)
    raw = RegistroCarteraRaw.objects.only('importacion_id').get(pk=reference.raw_id)
    ImportacionCartera.objects.select_for_update().get(pk=raw.importacion_id)
    s = RegistroCarteraStaging.objects.select_for_update().select_related('raw__importacion').get(pk=staging_id)
    if s.raw.importacion.aprobada or s.raw.importacion.estado not in ('COMPLETADO', 'COMPLETADO_CON_ADVERTENCIAS'):
        raise ValidationError('Solo puede revisar importaciones completadas y no aprobadas.')
    if not motivo.strip():
        raise ValidationError('Indique el fundamento de la decisión.')
    if decision not in ('ACEPTAR', 'EXCLUIR'):
        raise ValidationError('Decisión inválida.')
    allowed = {'ciu', 'cedula_ruc', 'nombres', 'clave', 'suministro', 'direccion', 'parroquia', 'telefono', 'correo', 'meses_deuda', *MONEY}
    if not set(valores).issubset(allowed):
        raise ValidationError('Campo no editable.')
    for key in ('ciu', 'cedula_ruc', 'clave', 'suministro'):
        if key in valores:
            valores[key] = identificador(valores[key])
    for key in MONEY:
        if key in valores:
            valores[key] = dinero(valores[key])
    before = {key: str(getattr(s, key)) for key in valores}
    before.update(predio=str(s.predio_id or ''), decision=s.decision)
    for key, value in valores.items():
        setattr(s, key, value)
    s.predio = predio
    if predio and predio.version_id != s.raw.importacion.catastro_version_id:
        raise ValidationError('El predio debe pertenecer al catastro usado en esta importación.')
    if decision == 'ACEPTAR' and (not predio or s.estado_validacion == 'REPETIDO'):
        raise ValidationError('Aceptar requiere predio. Una fila repetida solo se puede excluir.')
    if decision == 'ACEPTAR' and not predio.geometria_valida:
        raise ValidationError('La geometría está marcada inválida. Corrija una copia del catastro y use una nueva versión; no se altera el original.')
    s.estado_historico, s.proceso_coincidente = HistoricoMatcher(Expediente.objects.select_related('cliente', 'detalle')).match(data_staging(s), predio)
    if decision == 'ACEPTAR' and s.estado_historico in ('AMBIGUO', 'REQUIERE_REVISION'):
        raise ValidationError('El cruce histórico sigue ambiguo; revise los identificadores o excluya la fila.')
    s.fallecido = fallecido(s.nombres) or (predio is not None and fallecido(predio.nombres_catastro))
    s.estado_validacion = 'VALIDO' if s.estado_validacion != 'REPETIDO' else 'REPETIDO'
    s.estado_catastro = 'MANUAL' if predio else 'SIN_COINCIDENCIA'
    s.decision, s.motivo_revision = decision, motivo
    s.requiere_revision = False
    s.revisado_por, s.fecha_revision = usuario, timezone.now()
    s.save()
    registrar(usuario, 'CORRECCION_MANUAL', s, {'motivo': motivo}, before, {**{key: str(getattr(s, key)) for key in valores}, 'predio': str(s.predio_id or ''), 'decision': decision})
    return s

@transaction.atomic
def aprobar(importacion_id, usuario):
    exigir_rol(usuario, 'JEFE_FINANCIERA')
    imp = ImportacionCartera.objects.select_for_update().get(pk=importacion_id)
    if imp.aprobada:
        return 0
    if imp.estado not in ('COMPLETADO', 'COMPLETADO_CON_ADVERTENCIAS'):
        raise ValidationError('Espere a que termine el procesamiento.')
    # Se aprueba solo lo apto; las excepciones quedan visibles y preservadas.
    rows = RegistroCarteraStaging.objects.select_for_update(of=('self',)).filter(raw__importacion=imp, requiere_revision=False, estado_validacion='VALIDO').exclude(decision='EXCLUIR').select_related('predio', 'proceso_coincidente__cliente', 'raw')
    count = 0
    for s in rows:
        if s.proceso_coincidente:
            cliente = s.proceso_coincidente.cliente
        else:
            # No fusiona personas por cédula: cada nuevo caso conserva su entidad.
            cliente = Cliente.objects.create(cedula_ruc_original=str(s.raw.datos_originales.get('CEDULA_RUC') or ''), cedula_ruc_normalizada=s.cedula_ruc, nombres=s.nombres, fallecido=s.fallecido)
        values = {key: getattr(s, key) for key in ('ciu', 'suministro', 'clave', 'meses_deuda', *MONEY)}
        CarteraDetalle.objects.create(importacion=imp, staging=s, cliente=cliente, predio=s.predio, **values)
        count += 1
    if not count:
        raise ValidationError('No hay registros aptos para aprobar.')
    imp.aprobada = True
    imp.save(update_fields=['aprobada'])
    registrar(usuario, 'APROBACION', imp, {'snapshots': count, 'excepciones_preservadas': imp.filas_revision})
    return count
