# Arquitectura

Monolito modular orientado a servicios. Templates/FormViews son adaptadores HTTP; los servicios realizan validación, permisos, transacciones y auditoría. Los selectores encapsulan consultas filtradas. DRF expone solo consultas necesarias; no tiene CRUD de escritura.

Servicios Compose:

| Servicio | Responsabilidad | Persistencia |
|---|---|---|
| web | Django 6.1, Templates, API, migraciones development | media compartido |
| db | PostgreSQL 18 / PostGIS 3.6, verdad central | postgres_data |
| redis | Broker Celery | redis_data, AOF |
| worker | Importación/normalización/cruces en background | media compartido |

Redis no sustituye DB: el estado, errores y conteos de tareas viven en ImportacionCartera. El endpoint de progreso permite refrescar la UI sin bloquear upload.

Módulos: usuarios, clientes, catastro, financiera, procesos, ordenes, expedientes, preliminares, notificaciones, mapas, documentos, auditoria e integraciones. `core` contiene piezas transversales, salud y endpoints API de lectura. No hay microservicios HTTP por dominio.

Importaciones fijan la versión activa del catastro al iniciar el procesamiento. No cambia durante la tarea. CatastroMatcher precarga solo atributos, sin geometrías; HistoricoMatcher precarga expedientes y snapshots para evitar una consulta por fila. RAW/STAGING se escriben en lotes atómicos de 500.

Generación usa transacción, bloqueo asesor PostgreSQL compartido y restricciones únicas. Revalida histórico actual aun cuando la aprobación se haya realizado antes. Cambios de estado se serializan bloqueando expediente; resultados bloquean lote/expediente. No usa signals para reglas de negocio.

Archivos se almacenan mediante FileField/default_storage con copias privadas y SHA. PostgreSQL guarda metadata/rutas; no blobs de archivos. Mapas usan índices GiST, orden autorizada obligatoria y bbox transformado a 32717; las geometrías se serializan a 4326 en PostGIS. Máximo 2.000 features por consulta; si se excede, requiere acercar/filtrar.

El proveedor XYZ se configura con MAP_TILE_URL/MAP_TILE_ATTRIBUTION. Referrer-Policy strict-origin-when-cross-origin permite enviar solo el origen a proveedores externos y evita incluir rutas/identificadores. La configuración respeta la política del mapa base; los datos de cartera/expediente se sirven desde la aplicación, no se mandan al proveedor. Etiquetas usan número oficial cuando existe o los primeros ocho caracteres del UUID interno; el popup conserva la referencia completa.

Se prepara almacenamiento S3 en producción y adapter QGIS Server. Ambos son opcionales. ERP-CABILDO solo tiene un puente manual con estados; no se invoca el ERP.
