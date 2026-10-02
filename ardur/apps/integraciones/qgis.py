from dataclasses import dataclass

@dataclass(frozen=True)
class QgisPrintRequest:
    orden_id: str
    layout: str

class QgisServerAdapter:
    """Punto de extensión para GetPrint/Atlas; no se instala ni invoca en beta."""
    def print_url(self, request: QgisPrintRequest):
        raise NotImplementedError('QGIS Server no está configurado. Use la impresión del navegador.')
