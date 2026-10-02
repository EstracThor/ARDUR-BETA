# Validación ejecutada — 2 de octubre de 2026

## Entorno usado

- Windows, Python **3.14.0** aislado dentro de `.local/`.
- Django **6.1.1**, dependencias instaladas desde requirements.txt.
- PostgreSQL **18** / PostGIS **3.6.2**, clúster independiente del servidor existente, puerto local 55432.
- GDAL/GEOS/PROJ disponibles localmente; fixture GeoPackage de pruebas generada con ogr2ogr.
- Worker Celery real, pool solo y broker `memory://` **solo para pruebas y demostración local**. La configuración Compose usa Redis 8, no memory.

## Resultados

- **23 pruebas pasan**: importación/SHA, RAW/auditoría inmutables a nivel DB, fallecidos, matching ambiguo, procesos activos, órdenes múltiples/transacción completa, separación de roles, transferencia, asignaciones por usuario, resultados, documentos privados, CSRF, GeoPackage/SRID, GeoJSON filtrado y recorrido completo por formularios.
- Prueba adicional del worker real con conexión DB independiente y upload que se procesa fuera de la petición web.
- `manage.py check`: sin problemas.
- `manage.py makemigrations --check --dry-run`: sin cambios pendientes.
- Migraciones aplicadas a la base PostGIS local y a cada base de pruebas.
- Sintaxis JavaScript comprobada con Node; templates/renderización comprobados por pruebas y navegador.
- **CLI oficial Docker Compose 2.39.1: `config --quiet` pasa**, incluyendo resolución de variables `.env`, dependencias y volúmenes.
- Verificación final SHA-256: **4 de 4 originales intactos**; resultados en input-inspection.json.

## Archivos reales

- Catastro completo: **67.469 predios**, EPSG:32717, **13 geometrías inválidas preservadas** y marcadas. Importado en PostGIS mediante el comando real.
- Excel agosto completo procesado por Celery: **38.042 RAW**, **12.802 aptos**, **25.240 en revisión**, **0 errores**. Detalle de categorías en real-import-validation.json.
- Excel julio leído completo: **38.042 filas**, sin errores de normalización; advertencias de contenedor OLE registradas. No se modificó para corregirlo.
- Demostración local: aprobación de 12.802 snapshots, orden de **2 expedientes**, preliminares manuales, transferencia y lote con notificador. Un resultado está marcado explícitamente como demostración; **no se realizó notificación externa**. Referencias en demo-workflow-validation.json.

## Navegador

Ingreso como Financiera, dashboard con indicadores reales, ingreso como Notificaciones, orden y GeoJSON de sus dos predios, colores/etiquetas y cartografía base comprobados. Se ajustó Referrer-Policy para cumplir requisitos del proveedor OSM: solo origen en peticiones externas. Los documentos/cédulas/deudas no se envían al mapa base.

Capturas en screenshots/dashboard.jpg, screenshots/mapa.jpg y screenshots/mapa-imprimible.jpg. Vista imprimible de mapa revisada y botón IMPRIMIR MAPA habilitado tras cargar geometrías. La impresión está disponible mediante CSS/vista completa de lote; no se ejecutó una impresión física.

## Límite pendiente del entorno

**Este equipo no tiene Docker Engine/Desktop ni WSL instalado. No se ejecutó `docker compose up --build`, ni se validó el broker Redis dentro de contenedores.** La configuración Compose fue validada por su CLI oficial; el flujo y la suite se ejecutaron sobre Python 3.14/PostGIS reales con Celery. No se considera comprobado el despliegue Docker hasta ejecutar el comando en un equipo con contenedores Linux.

Los runtime/binarios locales, `.env`, `media` y los datos demo están excluidos de Git y de la imagen. README describe el arranque reproducible con Docker y Redis. No se instaló ni alteró PostgreSQL/QGIS/Docker/WSL del sistema.

## Evidencias locales y repositorio público

Los informes JSON y las capturas mencionados en este documento se conservan únicamente en el equipo de desarrollo y están excluidos del repositorio público porque proceden de datos reales. Los archivos de entrada, documentos privados, base de datos, credenciales y runtimes locales tampoco se distribuyen. Para ejecutar una instalación nueva, siga README y proporcione sus propios datos y credenciales.
