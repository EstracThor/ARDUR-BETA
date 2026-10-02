import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ardur.config.settings.development')
app = Celery('ardur')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
