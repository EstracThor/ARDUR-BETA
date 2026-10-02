"""Inspección read-only; ejecutable con el entorno Django/geográfico configurado."""
import os
import hashlib
import json
from pathlib import Path
from collections import Counter
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ardur.config.settings.development')
import django
django.setup()
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ValidationError
from ardur.apps.financiera.readers import filas_excel
from ardur.apps.financiera.normalization import normalizar

root = Path('data/input')
report = {}
for path in root.iterdir():
    if not path.is_file():
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    item = {'bytes': path.stat().st_size, 'sha256': digest}
    if path.suffix.lower() in ('.xls', '.xlsx'):
        counter, errors = Counter(), Counter()
        with filas_excel(path, 'Sheet 1') as rows:
            for number, original, source in rows:
                counter['filas'] += 1
                try:
                    data = normalizar(source)
                    counter['fallecidos_nombre'] += data['fallecido']
                except ValidationError as exc:
                    errors['; '.join(exc.messages)] += 1
        item.update(counter)
        item['errores_normalizacion'] = dict(errors)
    elif path.suffix.lower() == '.gpkg':
        ds = DataSource(str(path))
        item['capas'] = [{'nombre': layer.name, 'srid': layer.srs.srid, 'filas': layer.num_feat, 'campos': layer.fields} for layer in ds]
        invalid = []
        for feature in ds[0]:
            geometry = GEOSGeometry(feature.geom.wkt, srid=32717) if feature.geom else None
            if geometry is None or not geometry.valid:
                invalid.append(feature.fid)
        item['geometrias_invalidas'] = invalid
    report[path.name] = item
Path('docs').mkdir(exist_ok=True)
Path('docs/input-inspection.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({name: {key: value for key, value in info.items() if key != 'capas'} for name, info in report.items()}, ensure_ascii=False, indent=2))
