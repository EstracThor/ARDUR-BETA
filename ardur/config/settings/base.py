import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parents[3]
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    raise ImproperlyConfigured('Defina DJANGO_SECRET_KEY en el entorno.')
DEBUG = False
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
DOMAINS = ['core', 'usuarios', 'clientes', 'catastro', 'financiera', 'procesos', 'ordenes', 'expedientes', 'preliminares', 'notificaciones', 'mapas', 'documentos', 'auditoria', 'integraciones']
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'django.contrib.gis', 'rest_framework'] + [f'ardur.apps.{d}' for d in DOMAINS]
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'ardur.config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages', 'ardur.apps.usuarios.context_processors.roles']}}]
WSGI_APPLICATION = 'ardur.config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.contrib.gis.db.backends.postgis', 'NAME': os.environ.get('POSTGRES_DB', 'ardur'), 'USER': os.environ.get('POSTGRES_USER', 'ardur'), 'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''), 'HOST': os.environ.get('POSTGRES_HOST', 'db'), 'PORT': os.environ.get('POSTGRES_PORT', '5432'), 'CONN_MAX_AGE': 60}}
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
MAP_TILE_URL = os.environ.get('MAP_TILE_URL', 'https://tile.openstreetmap.org/{z}/{x}/{y}.png')
MAP_TILE_ATTRIBUTION = os.environ.get('MAP_TILE_ATTRIBUTION', '© OpenStreetMap contributors')
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/documentos/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/cuentas/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/cuentas/login/'
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 3600
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_TIMEOUT = 3
CELERY_TASK_PUBLISH_RETRY = False
ORDER_NUMBERING_STRATEGY = os.environ.get('ORDER_NUMBERING_STRATEGY', 'ardur.apps.ordenes.services.numbering.manual')
CASE_NUMBERING_STRATEGY = os.environ.get('CASE_NUMBERING_STRATEGY', 'ardur.apps.ordenes.services.numbering.manual')
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'], 'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'], 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination', 'PAGE_SIZE': 50}
for key in ('GDAL_LIBRARY_PATH', 'GEOS_LIBRARY_PATH'):
    if os.environ.get(key):
        globals()[key] = os.environ[key]
