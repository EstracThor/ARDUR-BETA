import tempfile
import time
from django.test import TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from celery.contrib.testing.worker import start_worker
from ardur.config.celery import app
from ardur.apps.financiera.services import subir
from ardur.apps.financiera.models import ImportacionCartera

class AsyncImportTests(TransactionTestCase):
    def test_real_celery_worker_processes_upload(self):
        from .test_workflow import WorkflowTests
        user = get_user_model().objects.create_user(username='async-fin')
        group, _ = Group.objects.get_or_create(name='JEFE_FINANCIERA')
        user.groups.add(group)
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp, CELERY_BROKER_URL='memory://', CELERY_RESULT_BACKEND=None):
            # Worker real en hilo y conexión DB independiente. Broker en memoria solo para tests.
            with start_worker(app, pool='solo', perform_ping_check=False, shutdown_timeout=10):
                imp = subir(WorkflowTests.excel(self), '2026-08', 'Sheet 1', user)
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    imp.refresh_from_db()
                    if imp.estado not in ('PENDIENTE', 'PROCESANDO'):
                        break
                    time.sleep(.1)
                self.assertEqual(imp.estado, 'COMPLETADO_CON_ADVERTENCIAS', imp.error)
                self.assertEqual(imp.total_filas, 2)
                self.assertEqual(imp.raw.count(), 2)
