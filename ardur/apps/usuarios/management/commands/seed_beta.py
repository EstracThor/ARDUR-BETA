import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

ROLE_APPS = {'JEFE_FINANCIERA': ['financiera', 'clientes', 'catastro', 'procesos', 'ordenes', 'expedientes', 'preliminares'], 'JEFE_NOTIFICACIONES': ['notificaciones'], 'NOTIFICADOR': [], 'CONSULTA': []}

class Command(BaseCommand):
    help = 'Crea roles y usuarios demo en desarrollo; requiere DEMO_PASSWORD explícita.'
    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('seed_beta solo está habilitado en development.')
        password = os.environ.get('DEMO_PASSWORD', '')
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError('Defina DEMO_PASSWORD: ' + '; '.join(exc.messages)) from exc
        admin_group, _ = Group.objects.get_or_create(name='ADMINISTRADOR')
        admin_group.permissions.set(Permission.objects.exclude(content_type__app_label__in=['auditoria']).exclude(codename__startswith='delete_registrocarteraraw'))
        for name, apps in ROLE_APPS.items():
            group, _ = Group.objects.get_or_create(name=name)
            if name == 'CONSULTA':
                perms = Permission.objects.filter(codename__startswith='view_', content_type__app_label__in=['ordenes', 'expedientes', 'notificaciones'])
            elif name == 'NOTIFICADOR':
                perms = Permission.objects.filter(codename__startswith='view_', content_type__app_label='notificaciones')
            else:
                perms = Permission.objects.filter(content_type__app_label__in=apps).exclude(codename__startswith='delete_').exclude(content_type__model='registrocarteraraw')
            group.permissions.set(perms)
        users = [('admin', 'ADMINISTRADOR'), ('financiera', 'JEFE_FINANCIERA'), ('notificaciones', 'JEFE_NOTIFICACIONES'), ('notificador1', 'NOTIFICADOR'), ('notificador2', 'NOTIFICADOR'), ('notificador3', 'NOTIFICADOR'), ('consulta', 'CONSULTA')]
        for username, role in users:
            user, created = get_user_model().objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.is_staff = role == 'ADMINISTRADOR'
                user.is_superuser = role == 'ADMINISTRADOR'
                user.save()
                user.groups.add(Group.objects.get(name=role))
            self.stdout.write(f'{username}: {role}; {"creado" if created else "existente (contraseña conservada)"}')
        self.stdout.write(self.style.WARNING('Usuarios DEMO de desarrollo; contraseña tomada de DEMO_PASSWORD, no se imprime.'))
