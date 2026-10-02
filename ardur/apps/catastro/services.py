from pathlib import Path
from decimal import Decimal
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.core.files import File
from django.core.exceptions import ValidationError
from django.db import transaction
from ardur.apps.documentos.services import sha256
from ardur.apps.financiera.normalization import texto
from .models import CatastroVersion, Predio

TEXT_FIELDS = ('provincia', 'canton', 'parroquia', 'zona', 'sector', 'manzana', 'predio', 'barrio', 'direccion', 'clave_ante', 'clave_nuev', 'predio_mun', 'clave_ag', 'cod_client', 'suministro', 'medidor')

@transaction.atomic
def importar_catastro(path, periodo, capa=None, activar=False):
    path = Path(path)
    with path.open('rb') as source:
        digest = sha256(source)
    if CatastroVersion.objects.filter(sha256=digest).exists():
        raise ValidationError('GeoPackage ya importado (SHA-256 existente).')
    datasource = DataSource(str(path))
    if capa:
        layer = datasource[capa]
    elif len(datasource) == 1:
        layer = datasource[0]
    else:
        raise ValidationError('Hay varias capas; especifique --capa. Disponibles: ' + ', '.join(l.name for l in datasource))
    if layer.srs is None or layer.srs.srid != 32717:
        raise ValidationError('Se exige CRS EPSG:32717; no se reproyecta el original silenciosamente.')
    required = {'parroquia', 'zona', 'sector', 'clave_ante', 'clave_nuev'}
    if not required.issubset(set(layer.fields)):
        raise ValidationError('Faltan atributos catastrales requeridos.')
    version = CatastroVersion.objects.create(nombre=path.name, periodo=periodo, sha256=digest)
    with path.open('rb') as source:
        version.archivo_origen.save(path.name, File(source), save=True)
    batch, count = [], 0
    for feature in layer:
        attrs = {field: feature.get(field) for field in layer.fields}
        if feature.geom is None:
            raise ValidationError(f'FID {feature.fid}: falta geometría.')
        geom = GEOSGeometry(feature.geom.wkt, srid=32717)
        if geom.geom_type == 'Polygon':
            geom = MultiPolygon(geom, srid=32717)
        if geom.geom_type != 'MultiPolygon' or geom.empty:
            raise ValidationError(f'FID {feature.fid}: se requiere MultiPolygon no vacío.')
        values = {field: texto(attrs.get(field)) for field in TEXT_FIELDS}
        values.update(nombres_catastro=texto(attrs.get('nombres')), ruc_cedula_catastro=texto(attrs.get('ruc_cedula')))
        for field in ('total_deud', 'deuda_mese'):
            value = attrs.get(field)
            values[field] = Decimal(str(value)).quantize(Decimal('0.01')) if value is not None else None
        batch.append(Predio(version=version, source_fid=str(feature.fid), atributos_originales=attrs, geom=geom, geometria_valida=geom.valid, **values))
        count += 1
        if len(batch) >= 1000:
            Predio.objects.bulk_create(batch)
            batch = []
    Predio.objects.bulk_create(batch)
    if activar:
        # Bloqueo común serializa activaciones concurrentes incluso con distintas versiones.
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(32717)')
        CatastroVersion.objects.filter(activo=True).update(activo=False)
        version.activo = True
        version.save(update_fields=['activo'])
    return version, count
