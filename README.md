# ARDUR S.A. — Beta funcional

Monolito modular Django para importar cartera, depurar cruces catastrales/históricos, crear órdenes con expedientes, registrar preliminares externas y planificar notificaciones. Interfaz en español mediante Templates, Bootstrap y Leaflet. PostgreSQL/PostGIS es la única base de datos.

## Requisitos

- Docker Engine / Docker Desktop con Compose v2 y contenedores Linux.
- Aproximadamente 4 GB de RAM disponibles; espacio adicional para archivos y base de datos.
- Archivos originales en `data/input/`. Compose los monta como solo lectura.
- Internet para descargar imágenes y dependencias inicialmente, y para el mapa base OpenStreetMap. CSS/JS están incluidos localmente.

Versiones: Python 3.14, Django 6.1.1, DRF 3.18.1, PostgreSQL 18, PostGIS 3.6, Celery 5.6.3 y Redis 8. El contenedor incluye GDAL/GEOS/PROJ. No requiere QGIS Desktop.

## Instalación desde cero

1. Si todavía no tiene `.env`, copie `.env.example` a `.env` (`Copy-Item .env.example .env` en PowerShell). Conserve su archivo existente si ya está configurado.
2. Edite `.env`: cambie `POSTGRES_PASSWORD`, defina una `DJANGO_SECRET_KEY` aleatoria y una `DEMO_PASSWORD` propia de al menos 12 caracteres. No publique `.env`.
3. Ejecute:

```sh
docker compose up --build -d
docker compose ps
docker compose logs -f web worker
```

`web` aplica migraciones y recopila estáticos antes de arrancar. `worker` espera al healthcheck de web, que comprueba conexión a DB. El primer arranque puede tardar mientras se construye la imagen.

Si está usando la demostración local preparada durante el desarrollo, deténgala antes de levantar Docker en el mismo puerto: `& .local/stop_demo.ps1` en PowerShell. Esa demostración usa una base local independiente; los contenedores se inicializan e importan por separado siguiendo los pasos siguientes.

4. Compruebe migraciones y configuración:

```sh
docker compose exec web python manage.py check
docker compose exec web python manage.py migrate --noinput
docker compose exec web python manage.py makemigrations --check --dry-run
```

5. Importe el catastro **antes de subir cartera**:

```sh
docker compose exec web python manage.py import_catastro data/input/Catastro_unido_agosto.gpkg --periodo 2026-08 --activar
```

El comando detecta la capa, exige EPSG:32717, copia el archivo a almacenamiento privado, calcula SHA-256, conserva atributos/geometrías originales y activa la versión solo al completar la transacción. Los 13 predios inválidos del archivo suministrado se conservan con marca de revisión.

6. Cree los roles y usuarios demo:

```sh
docker compose exec web python manage.py seed_beta
```

Usuarios: `admin`, `financiera`, `notificaciones`, `notificador1`, `notificador2`, `notificador3`, `consulta`. Su contraseña inicial es la `DEMO_PASSWORD` que usted definió. El comando no reinicia contraseñas de usuarios existentes y se niega a ejecutarse en producción. Administrador puede crear usuarios reales en `/admin/`; los jefes no tienen acceso de escritura al admin.

7. Abra [http://localhost:8000](http://localhost:8000), ingrese con `financiera` y use **Nueva importación**. Para ambos Excel suministrados seleccione `Sheet 1`; indique `2026-07` o `2026-08` según corresponda. No use hojas unificadas como cartera original.

## Recorrido de demostración

1. Financiera: subir Excel → observar procesamiento → abrir depuración y filtros.
2. Revisar excepciones: inspeccionar RAW, candidatos y fundamento; aceptar con predio válido o excluir conservando RAW. Puede buscar un predio por clave/código y copiar su UUID.
3. Aprobar los registros aptos. Se crea el snapshot mensual; los pendientes quedan documentados y fuera de las órdenes.
4. **Preparar órdenes**: seleccionar agrupaciones por parroquia/zona/sector y generar. Cada grupo produce una orden con varios expedientes; los procesos activos quedan fuera.
5. Abrir orden/expediente y opcionalmente registrar números oficiales suministrados por el negocio.
6. Registrar preliminar generada externamente en ERP-CABILDO (PDF opcional, títulos/recargo reportados).
7. Marcar cada expediente **LISTO PARA NOTIFICAR**.
8. Cerrar sesión; ingresar con `notificaciones`. Abrir órdenes transferidas y su mapa.
9. Crear lote: fecha, expedientes listos y notificador. Repetir para otro notificador cuando corresponda.
10. Imprimir mapa y listado completo, registrar resultado desde el lote y consultar auditoría.

Un notificador solo consulta casos/lotes asignados. Los resultados se administran por el jefe, conforme al alcance de la beta. Consulta es de lectura sobre expedientes transferidos.

## Rutas principales

| Ruta | Función |
|---|---|
| `/cuentas/login/` | Autenticación |
| `/financiera/` | Dashboard financiera |
| `/financiera/carteras/` | Importaciones e histórico mensual |
| `/financiera/importar/` | Upload Excel |
| `/financiera/carteras/<uuid>/` | Depuración, excepciones, progreso y aprobación |
| `/financiera/carteras/<uuid>/ordenes/` | Vista territorial previa |
| `/financiera/ordenes/` | Órdenes / expedientes |
| `/financiera/expedientes/` | Histórico de procesos y preliminares |
| `/notificaciones/` | Dashboard notificaciones |
| `/notificaciones/ordenes/` | Casos transferidos |
| `/notificaciones/mapa/?orden=<uuid>` | Mapa filtrado |
| `/notificaciones/lotes/` | Planificación / resultados / impresión |
| `/auditoria/` | Eventos inmutables |
| `/api/v1/{health,ordenes,expedientes,lotes}/` | API autenticada de lectura |
| `/api/v1/mapa/geojson/?orden=<uuid>&bbox=o,s,e,n` | Geometrías EPSG:4326 autorizadas |
| `/health/` | Salud pública sin datos sensibles |

Los documentos solo se sirven mediante vistas con permisos; no se publica `media/` directamente.

## Pruebas

```sh
docker compose exec web python manage.py test ardur.apps.core.tests -v 2
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
```

La suite usa una base PostgreSQL/PostGIS de pruebas, fixtures pequeñas y temporales. Comprueba SHA duplicado, RAW y auditoría inmutables, fallecidos, casos activos/ambiguos, órdenes múltiples, estados y permisos, GeoPackage/SRID y GeoJSON por orden. El usuario DB de desarrollo necesita `CREATEDB` para ejecutar tests. Consulte `docs/validation.md` para resultados y limitaciones del entorno realmente usado.

Para inspeccionar los archivos sin importarlos: `docker compose exec web python -m scripts.inspect_inputs`. Genera `docs/input-inspection.json` (resumen sin nombres ni cédulas).

## Estructura y modelos

```text
ardur/
  config/settings/                 base / development / production
  config/                         urls, asgi, wsgi, celery
  apps/
    core/                         salud, API, admin de lectura, tests
    usuarios/                     roles, permisos, seed_beta
    clientes/                     Cliente
    catastro/                     CatastroVersion, Predio, import_catastro
    financiera/                   ImportacionCartera, RAW, Staging, CarteraDetalle
    procesos/                     matching conservador
    ordenes/                      Orden, servicios, estrategia numbering
    expedientes/                  Expediente, cierre/numeración
    preliminares/                 Preliminar, ReglaRecargo (reserva futura)
    notificaciones/               LoteNotificacion, AsignacionNotificador
    mapas/                        consultas espaciales e impresión
    documentos/                   hashing, validación, descargas privadas
    auditoria/                    EventoAuditoria append-only
    integraciones/                adapter futuro QGIS Server
templates/                        interfaz Django en español
static/                           estilos, Bootstrap, Leaflet, mapa
docs/                             arquitectura, BD, reglas y validación
scripts/                          arranque e inspección
data/input/                       originales intactos; solo lectura en Docker
Dockerfile / docker-compose.yml / .env.example / requirements.txt
```

## Operación y producción futura

`docker compose stop` conserva volúmenes. `docker compose down` conserva datos salvo que agregue `-v` (no usar si desea conservarlos). Respaldar DB con `pg_dump` y almacenar también los archivos `media`. Restaurar ambos de forma consistente.

Development utiliza runserver. Para producción configure `ardur.config.settings.production`, secretos, hosts, HTTPS con proxy explícitamente configurado, Gunicorn (`gunicorn ardur.config.wsgi:application --bind 0.0.0.0:8000`), servidor de estáticos, backups y credenciales DB con privilegios mínimos. `S3_BUCKET` y opcional `S3_ENDPOINT_URL` activan almacenamiento S3 privado; las credenciales provienen de variables/rol IAM, nunca del código. La ejecución de migraciones debe ser un paso de despliegue controlado, no varios procesos concurrentes.

Documentación: `docs/architecture.md`, `docs/database.md`, `docs/import-financiera.md`, `docs/catastro.md`, `docs/qgis.md`, `docs/business-rules.md`, `docs/beta-scope.md`.
