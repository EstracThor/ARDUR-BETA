from .base import *
DEBUG = False
if SECRET_KEY.startswith('development') or len(SECRET_KEY) < 50:
    raise ImproperlyConfigured('Producción requiere una clave aleatoria de al menos 50 caracteres.')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
if os.environ.get('S3_BUCKET'):
    STORAGES = {'default': {'BACKEND': 'storages.backends.s3.S3Storage', 'OPTIONS': {'bucket_name': os.environ['S3_BUCKET'], 'endpoint_url': os.environ.get('S3_ENDPOINT_URL'), 'default_acl': 'private', 'querystring_auth': True}}, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'}}
