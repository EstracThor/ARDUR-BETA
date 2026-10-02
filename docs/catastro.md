# Catastro versionado

```sh
docker compose exec web python manage.py import_catastro data/input/Catastro_unido_agosto.gpkg --periodo 2026-08 --activar
```

Una capa detectada: `catastro_unido`, 67.469 features, MULTIPOLYGON, EPSG:32717. Si hay más de una capa, use `--capa nombre`. Sin CRS correcto se rechaza el archivo. No se modifica ni reproyecta el GeoPackage fuente.

Se preservan todos los atributos en JSON y los campos frecuentes como columnas indexadas; `nombres` se mapea a nombres_catastro y `ruc_cedula` a ruc_cedula_catastro. Los importes catastrales se convierten a Decimal usando su representación textual; el atributo original permanece en JSON.

El catastro suministrado tiene 13 geometrías inválidas: FID 162, 12934, 15051, 26406, 27029, 30943, 31953, 44229, 49700, 52320, 54421, 56129, 61583. Se importan intactas con geometria_valida=False. Los casos relacionados se llevan a revisión; no se aplica MakeValid ni buffer automático. Para corregir, prepare y revise una **copia**, importe una nueva versión y procese cartera con esa versión. Los snapshots previos conservan su referencia original.

SHA-256 único protege contra repetir exactamente el mismo GeoPackage. Activación al final de transacción deja una sola versión activa; una nueva versión no elimina las anteriores. Originales privados se guardan en media/catastro o S3 configurado. Un fallo de transacción puede dejar una copia huérfana en almacenamiento: se debe revisar antes de limpiar, nunca borrar originales de data/input.

API web transforma a 4326 en PostGIS. La DB y QGIS usan 32717. No se envían 67.469 geometrías al navegador.
