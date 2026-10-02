import re
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from ardur.apps.catastro.services import importar_catastro

class Command(BaseCommand):
    help = 'Importa GeoPackage EPSG:32717 sin modificarlo.'
    def add_arguments(self, parser):
        parser.add_argument('ruta')
        parser.add_argument('--periodo', required=True, help='AAAA-MM')
        parser.add_argument('--capa')
        parser.add_argument('--activar', action='store_true')
    def handle(self, *args, **options):
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', options['periodo']):
            raise CommandError('Periodo inválido; use AAAA-MM.')
        try:
            version, count = importar_catastro(options['ruta'], options['periodo'], options['capa'], options['activar'])
        except (ValidationError, OSError) as exc:
            raise CommandError(str(exc)) from exc
        invalid = version.predio_set.filter(geometria_valida=False).count()
        self.stdout.write(self.style.SUCCESS(f'Versión {version.pk}: {count} predios; {invalid} geometrías inválidas preservadas para revisión; SRID 32717; SHA {version.sha256}; activa={version.activo}'))
