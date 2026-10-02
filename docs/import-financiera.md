# Importación financiera

Archivos inspeccionados: julio `.xls` (BIFF/OLE) y agosto `.xlsx`. Ambos: `Sheet 1`, 38.042 filas, encabezados CIU, CEDULA_RUC, NOMBRES, CLAVE, DIRECCION, PARROQUIA, TELEF, CORREO, TOTAL_EMISION, TOTAL_INTERES, TOTAL_COACTIVA, TOTAL_RECARGO, MESES_DEUDA. Agosto tiene además cuatro hojas auxiliares; no se importan automáticamente. Julio muestra advertencias del contenedor OLE pero xlrd lee todas las filas.

Pipeline: upload privado + SHA → tarea Celery → fila RAW JSONB → normalización/validación Decimal → cruce de catastro versionado → cruce de expedientes → staging → revisión auditada → aprobación → snapshots → selección territorial → órdenes/expedientes.

Los strings preservan ceros iniciales. Cuando Excel almacena un número con formato exclusivo de ceros, se usa la máscara para staging; RAW conserva el valor almacenado y el archivo original conserva formato/tipos. Si el origen convirtió un identificador a número sin máscara, los ceros perdidos no pueden reconstruirse: no se inventan. CIU/cod_client se comparan también sin relleno inicial solo para buscar candidatos; la unión de señales e identidad deben ser coherentes.

Dinero usa Decimal(str(valor)) con dos decimales; separadores ambiguos, fórmulas, negativos o valores fuera de rango pasan a error. El archivo original y RAW nunca cambian. No se corrige la codificación de nombres automáticamente: algunos textos del origen contienen caracteres de reemplazo. Se conserva el nombre recibido.

Filas exactamente repetidas se conservan y la segunda queda en revisión. No se suman valores ni se consolida por cédula. Las distintas filas de un mismo caso se revalidan al generar; si intentan crear dos expedientes activos, se revierte toda la generación del grupo y se indica revisión.

Matching usa claves catastrales y CIU/cod_client para candidatos. No asume que CIU/suministro sean iguales. La parte anterior a `/` en CLAVE compuesta solo propone candidatos. Si distintos identificadores apuntan a diferentes predios, hay ambigüedad. Cédula distinta del catastro produce conflicto. No se selecciona por nombre parecido ni por cédula sola.

Sin catastro, geometría inválida, ambigüedad, procesos cerrados y posible nueva deuda requieren revisión. PROCESO_ACTIVO puede producir snapshot mensual de deuda ligado al cliente existente, pero nunca candidato a expediente nuevo. POSIBLE_NUEVA_DEUDA es solo una advertencia por aumento de importe contra el snapshot del expediente cerrado, no una determinación legal/financiera de nueva obligación.

Revisar permite corregir staging, elegir un predio de la misma versión, aceptar con fundamento o excluir. Una fila repetida solo admite exclusión; una geometría inválida no admite aprobación automática/manual como apta. La revisión original siempre queda auditada. Aprobar toma únicamente filas aptas, preserva las excepciones y cierra la importación para nuevas decisiones. Para pendientes se necesita una posterior cartera/nueva versión; no se reabre un snapshot aprobado.

Estados PENDIENTE, PROCESANDO, COMPLETADO, COMPLETADO_CON_ADVERTENCIAS, ERROR. Fallos de broker/worker quedan en DB con mensaje y en logs. Se puede reintentar ERROR sin borrar RAW. Si el worker es terminado abruptamente fuera del manejo normal, un administrador debe comprobar logs/tarea antes de restablecer una importación atascada; no hay reintento ciego automático.
