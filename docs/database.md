# Base de datos e integridad

Todos los modelos de negocio tienen UUID interno y fecha_creacion. Los identificadores externos no son PK ni únicos. Se indexan cédula normalizada, CIU, claves, suministro y territorio compuesto. Predio.geom es MultiPolygon EPSG:32717 con índice espacial GiST.

- Cliente: identidad original/normalizada, nombre preservado y fallecido. No se fusiona por cédula.
- CatastroVersion: archivo privado, periodo, SHA único y una sola versión activa mediante restricción parcial.
- Predio: versión/FID únicos, campos originales catastrales, JSON de todos los atributos y geometría original; geometria_valida identifica excepciones sin repararlas.
- ImportacionCartera: archivo/SHA únicos, usuario, hoja, versión usada, estados/conteos/error y aprobación.
- RegistroCarteraRaw: fila original JSONB, número de fila único por importación; trigger rechaza UPDATE y DELETE.
- RegistroCarteraStaging: relación 1:1 RAW, valores normalizados Decimal, clasificación, candidatos, decisión/fundamento y revisor.
- CarteraDetalle: snapshot aprobado 1:1 staging con cliente/predio, identificadores y deuda mensual.
- Orden: parroquia/zona/sector, UUID, numero_negocio opcional y creador.
- Expediente: caso individual, orden 1:N, detalle 1:1, estado y fingerprint del caso. Restricción parcial impide fingerprint duplicado mientras no esté CERRADO.
- Preliminar: 1:1 expediente, PDF/SHA opcionales, fuente ERP_CABILDO, cantidades/recargo reportados y autor/fecha.
- ReglaRecargo: reserva de configuración futura; no se ejecuta ninguna fórmula.
- LoteNotificacion: orden, fecha, responsable y estado.
- AsignacionNotificador: expediente 1:1, lote, notificador, resultado y observaciones. No permite doble asignación.
- EventoAuditoria: actor/hora/acción/entidad/id/metadata/antes/después. Trigger rechaza UPDATE y DELETE; admin solo lectura.

Relaciones de negocio usan PROTECT. No hay cascadas que borren RAW, snapshots o histórico. El administrador de DB sigue teniendo privilegios para mantenimiento: en producción usar cuentas separadas para migración y operación, backups y controles de acceso al servidor.

El fingerprint no reemplaza matching: protege un caso ya elegido. Matching busca señales de predio/suministro/CIU/claves y revisa identidad; el servicio vuelve a consultar todos los procesos antes de crear. Índices permiten consultar histórico sin declarar únicos los identificadores externos.
