from django.core.management.base import BaseCommand
from apps.surveys.data_loaders import load_all_initial_data, create_initial_data_file

class Command(BaseCommand):
    help = 'Carga los datos iniciales para el módulo de encuestas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-file',
            action='store_true',
            help='Crea el archivo indicador de datos iniciales para que se carguen en el próximo inicio',
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la carga de datos iniciales incluso si ya existen',
        )

    def handle(self, *args, **options):
        if options['create_file']:
            # Crear archivo para carga en el próximo inicio
            result = create_initial_data_file()
            if result['success']:
                self.stdout.write(self.style.SUCCESS(result['message']))
                self.stdout.write(self.style.SUCCESS(
                    'Los datos se cargarán automáticamente en el próximo inicio de la aplicación'
                ))
            else:
                self.stdout.write(self.style.ERROR(result['message']))
        else:
            # Cargar datos inmediatamente
            self.stdout.write(self.style.WARNING('Iniciando carga de datos iniciales...'))
            results = load_all_initial_data()
            
            # Mostrar resultados
            success_count = sum(1 for r in results.values() if r['success'])
            if success_count == len(results):
                self.stdout.write(self.style.SUCCESS('Todos los datos se cargaron correctamente'))
            else:
                self.stdout.write(self.style.WARNING(
                    f'Se cargaron {success_count} de {len(results)} tipos de datos'
                ))
                
            # Detalles de cada tipo de datos
            for data_type, result in results.items():
                if result['success']:
                    self.stdout.write(self.style.SUCCESS(f"✅ {data_type}: {result['message']}"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ {data_type}: {result['message']}"))
