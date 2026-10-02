# Reglas de negocio

## CONFIRMADO

- PostgreSQL/PostGIS central; IDs internos, identificadores externos no únicos.
- Originales/RAW preservados; dinero Decimal; ninguna fusión por cédula sola.
- Orden contiene varios expedientes; territorio se compone de parroquia/zona/sector.
- Proceso activo impide expediente nuevo automáticamente. Ambiguos requieren revisión.
- `+` y `(+)` marcan fallecido sin excluir ni impedir el proceso.
- ERP-CABILDO externo/manual, PDF opcional; ninguna automatización del ERP.
- Generación externa → preliminar registrada → transferencia explícita a LISTO_PARA_NOTIFICAR.
- Notificaciones no recibe casos previos a esa transferencia; roles y alcance de asignaciones protegidos.
- Jefe de Notificaciones administra resultados; beta sin móvil ni optimización de rutas.
- Recargo reportado se almacena; no se fija fórmula de $0.15 por título.
- Todas las decisiones y transiciones críticas se auditan.

## HIPÓTESIS (ENCAPSULADAS)

- La primera hoja `Sheet 1` es la cartera original, comprobada contra encabezados reales; el usuario puede indicar otra hoja compatible.
- CIU puede corresponder a cod_client con distinto relleno de ceros. CLAVE anterior a `/` puede corresponder a una clave catastral. Se usan solo como señales de candidatos; señales contradictorias o cédula distinta exigen revisión. Motor: `procesos/services.py`.
- Aumento del total contra snapshot de un expediente cerrado se etiqueta POSIBLE_NUEVA_DEUDA para revisión. No autoriza abrir caso por sí solo.
- Nuevos casos conservan una entidad Cliente propia cuando no hay vínculo histórico inequívoco. No se consolida automáticamente una persona por cédula.
- Aprobación cierra decisiones de esa importación, creando solo snapshots aptos. Excepciones quedan fuera y preservadas; resolver antes de aprobar si se quieren incorporar al mismo periodo.
- Geometría inválida se conserva y no admite generación de caso hasta usar una versión corregida.
- Una asignación por expediente en esta beta; no hay reprogramación ni múltiples intentos modelados.
- Cierre manual por Financiera requiere fundamento y lote sin resultado pendiente; no infiere pago ni automatiza reglas legales de cierre.
- CONSULTA puede leer solo datos transferidos, sin valores financieros ni RAW.

## PENDIENTE DE DEFINIR

1. Formato definitivo de número de Orden.
2. Formato definitivo de número de Expediente.
3. Reglas exactas de la plantilla depurada, consolidación/exportación oficial.
4. Integración ERP-CABILDO (fuera de beta).
5. Regla definitiva de $0.15 por título y otros recargos.
6. Tratamiento final de determinados casos de nueva deuda tras proceso cerrado.

Numeración beta usa UUID interno y campo numero_negocio editable. Estrategias en `ordenes/services/numbering.py` y `expedientes/numbering.py`; no producen nomenclaturas oficiales inventadas. ReglaRecargo reserva configuración futura y no se evalúa.
