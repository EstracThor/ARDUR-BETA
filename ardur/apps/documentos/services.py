import hashlib
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError

def sha256(archivo):
    digest = hashlib.sha256()
    archivo.seek(0)
    for chunk in iter(lambda: archivo.read(1024 * 1024), b''):
        digest.update(chunk)
    archivo.seek(0)
    return digest.hexdigest()

def validar_archivo(archivo, extensiones):
    if Path(archivo.name).suffix.lower() not in extensiones:
        raise ValidationError('Extensión de archivo no admitida.')
    if archivo.size > settings.MAX_UPLOAD_BYTES:
        raise ValidationError('El archivo excede el límite de 100 MB.')
    if '.pdf' in extensiones:
        archivo.seek(0)
        if archivo.read(5) != b'%PDF-':
            archivo.seek(0)
            raise ValidationError('El contenido no corresponde a un PDF.')
        archivo.seek(0)
