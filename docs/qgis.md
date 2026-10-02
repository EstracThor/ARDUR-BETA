# QGIS Desktop con PostgreSQL/PostGIS

QGIS Desktop no es dependencia de la aplicación. `data/input/equisde.qgz` queda intacto como referencia cartográfica; no se modifica para apuntar a DB automáticamente.

1. Arranque Compose e importe el catastro.
2. QGIS → Administrador de fuentes de datos → PostgreSQL → Nueva conexión.
3. Nombre: ARDUR local. Host: localhost. Puerto: **5433** (publicado por Compose). Base/usuario/contraseña: valores de `.env`.
4. Pruebe conexión, conecte y agregue `public.catastro_predio`, columna `geom`.
5. Establezca CRS de la capa/proyecto EPSG:32717. Filtre version_id por la versión deseada; los identificadores externos pueden repetirse.

El puerto DB solo se publica en loopback. No comparta credenciales demo ni use cuenta de escritura en puestos de consulta. Para lectura en QGIS, un administrador puede crear un rol dedicado:

```sql
CREATE ROLE ardur_qgis LOGIN;
-- Defina la contraseña por un canal seguro (por ejemplo \password ardur_qgis en psql).
GRANT CONNECT ON DATABASE ardur TO ardur_qgis;
GRANT USAGE ON SCHEMA public TO ardur_qgis;
GRANT SELECT ON catastro_predio, catastro_catastroversion TO ardur_qgis;
```

No editar directamente las tablas de cartera/expedientes desde QGIS: el flujo de aplicación registra validaciones y auditoría. Las correcciones cartográficas se realizan sobre copias/versiones nuevas.

Impresión beta usa Leaflet + CSS del navegador. Mejora futura: QGIS Server WMS/GetPrint y Atlas con plantilla oficial, detrás de `apps/integraciones/qgis.py`. No se instala QGIS Server y su adapter indica explícitamente que aún no está configurado.
