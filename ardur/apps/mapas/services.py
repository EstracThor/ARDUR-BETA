import json
import math
from django.contrib.gis.db.models.aggregates import Extent
from django.contrib.gis.geos import Polygon
from django.contrib.gis.db.models.functions import Transform, AsGeoJSON
from django.core.exceptions import ValidationError
from ardur.apps.notificaciones.selectors import expedientes_visibles

def casos_mapa(usuario, orden, lote=None, territorio=None):
    qs = expedientes_visibles(usuario).filter(orden=orden, predio__isnull=False)
    if lote:
        qs = qs.filter(asignacion__lote=lote)
    if territorio:
        for field in ('parroquia', 'zona', 'sector'):
            if territorio.get(field):
                qs = qs.filter(**{f'predio__{field}': territorio[field]})
    return qs

def geojson(usuario, orden, bbox=None, lote=None, territorio=None):
    qs = casos_mapa(usuario, orden, lote, territorio)
    if bbox:
        try:
            bounds = [float(v) for v in bbox.split(',')]
        except (ValueError, AttributeError) as exc:
            raise ValidationError('bbox debe contener oeste,sur,este,norte.') from exc
        if len(bounds) != 4 or not all(math.isfinite(v) for v in bounds) or not (-180 <= bounds[0] < bounds[2] <= 180 and -90 <= bounds[1] < bounds[3] <= 90):
            raise ValidationError('bbox inválido.')
        polygon = Polygon.from_bbox(bounds)
        polygon.srid = 4326
        polygon.transform(32717)
        qs = qs.filter(predio__geom__intersects=polygon)
    if qs.count() > 2000:
        raise ValidationError('La selección supera 2.000 predios. Filtre territorio o acerque el mapa.')
    qs = qs.annotate(geometria=AsGeoJSON(Transform('predio__geom', 4326))).values('id', 'numero_negocio', 'estado', 'predio__direccion', 'geometria')
    return {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'geometry': json.loads(row['geometria']), 'properties': {'expediente': row['numero_negocio'] or str(row['id']), 'etiqueta_mapa': row['numero_negocio'] or str(row['id'])[:8], 'estado': row['estado'], 'direccion': row['predio__direccion']}} for row in qs]}

def extension(usuario, orden, lote=None):
    extent = casos_mapa(usuario, orden, lote).aggregate(bbox=Extent(Transform('predio__geom', 4326)))['bbox']
    return list(extent) if extent else None
