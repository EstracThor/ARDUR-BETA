# Alcance beta

Incluye importadores reales .xls/.xlsx/GeoPackage, versionado y archivo privado, Celery, RAW/staging, revisión, snapshot, matching conservador, órdenes/expedientes, preliminar manual y PDF, transferencia, mapa filtrado, lotes/asignaciones, resultados, impresión, roles, API de lectura, auditoría, migraciones y tests.

No incluye ERP automatizado, fórmulas de recargo, nomenclatura oficial inventada, móvil, optimización de rutas, pagos, notificación legal automática, exportación de plantilla oficial no definida ni QGIS Server obligatorio.

Datos originales están disponibles localmente para importación manual autorizada; no se cargan ni se crean credenciales inseguras silenciosamente al iniciar Docker. El comando seed_beta exige contraseña explícita y environment development.

Limitaciones prácticas: mapa base requiere Internet; impresión se verifica visualmente por el operador y usa las geometrías visibles; grupos con más de 2.000 predios requieren zoom/bbox. Excel se procesa por worker único por importación; cierre abrupto puede necesitar intervención administrativa. No hay reenvíos de notificación ni reapertura de una importación aprobada. La interfaz usa tablas paginadas y el listado imprimible usa todos los casos autorizados del lote.

La aceptación requiere el recorrido completo descrito en README y pruebas sin fallos. El arranque Compose se debe comprobar en un equipo con Docker; la ausencia de Docker en el entorno de construcción se reporta expresamente en validación y no se presenta como prueba ejecutada.
