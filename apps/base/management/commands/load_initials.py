from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import time
import importlib
import sys
import os

class Command(BaseCommand):
    help = 'Carga inicial de datos para el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--module',
            type=str,
            choices=['geography', 'puc', 'types', 'all'],
            default='all',
            help='Especificar el módulo a cargar: geography, puc, types o all (todos)'
        )
        
        parser.add_argument(
            '--level',
            type=str,
            default='all',
            help='Nivel específico a cargar para el módulo seleccionado'
        )
        
        parser.add_argument(
            '--batch',
            type=int,
            default=100,
            help='Tamaño del lote para carga masiva'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la carga aunque ocurran errores'
        )

    def handle(self, *args, **options):
        module = options['module']
        level = options['level']
        batch_size = options['batch']
        force = options['force']
        
        start_time = time.time()
        self.stdout.write(self.style.MIGRATE_HEADING(f"Iniciando carga inicial de datos - Módulo: {module}, Nivel: {level}"))
        
        # Configurar orden de ejecución
        modules_to_load = []
        
        if module == 'all' or module == 'geography':
            modules_to_load.append({
                'name': 'geography',
                'import_path': 'apps.base.management.commands.load_geography',
                'command_class': 'Command',
                'order': 1,
                'description': 'Datos geográficos (países, estados, ciudades)'
            })
            
        if module == 'all' or module == 'types':
            modules_to_load.append({
                'name': 'types',
                'import_path': 'apps.base.management.commands.load_types',
                'command_class': 'Command',
                'order': 2,
                'description': 'Tipos y catálogos del sistema'
            })
            
        if module == 'all' or module == 'puc':
            modules_to_load.append({
                'name': 'puc',
                'import_path': 'apps.accounting.management.commands.load_puc',
                'command_class': 'Command',
                'order': 3,
                'description': 'Plan Único de Cuentas (PUC)'
            })
        
        # Ordenar por prioridad
        modules_to_load.sort(key=lambda x: x['order'])
        
        success_count = 0
        error_count = 0
        
        # Ejecutar cada módulo en orden
        for module_info in modules_to_load:
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"\n[{module_info['order']}] Cargando {module_info['description']}..."
            ))
            
            try:
                # Importar dinámicamente el módulo
                module_path = module_info['import_path']
                command_class_name = module_info['command_class']
                
                try:
                    module_import = importlib.import_module(module_path)
                    command_class = getattr(module_import, command_class_name)
                except (ImportError, AttributeError) as e:
                    self.stdout.write(self.style.ERROR(
                        f"❌ Error al importar el módulo {module_path}: {str(e)}"
                    ))
                    error_count += 1
                    if not force:
                        continue
                
                # Crear instancia del comando y ejecutarlo
                command = command_class()
                command.stdout = self.stdout  # Pasar el stdout para mantener el formato de salida
                
                # Preparar argumentos
                cmd_options = {
                    'level': level,
                    'batch': batch_size
                }
                
                # Ejecutar comando
                command.handle(**cmd_options)
                success_count += 1
                
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Módulo {module_info['name']} cargado correctamente"
                ))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"❌ Error al cargar el módulo {module_info['name']}: {str(e)}"
                ))
                error_count += 1
                if not force:
                    self.stdout.write(self.style.WARNING(
                        "Interrumpiendo la carga. Use --force para continuar a pesar de los errores."
                    ))
                    break
        
        # Reporte final
        elapsed_time = time.time() - start_time
        self.stdout.write("\n" + "="*70)
        if error_count == 0:
            self.stdout.write(self.style.SUCCESS(
                f"✅ CARGA INICIAL COMPLETADA EXITOSAMENTE en {elapsed_time:.2f} segundos"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠️ CARGA INICIAL FINALIZADA CON ADVERTENCIAS en {elapsed_time:.2f} segundos"
            ))
            self.stdout.write(self.style.WARNING(
                f"   {success_count} módulos cargados correctamente, {error_count} módulos con error"
            ))
        self.stdout.write("="*70)