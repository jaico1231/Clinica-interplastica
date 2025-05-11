#!/usr/bin/env python
import os
import shutil
import sys
import django
from pathlib import Path
from importlib import import_module
from django.core.management import call_command

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.conf import settings

# Definir el directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent

def borrar_migraciones():
    """Elimina los archivos de migración de todas las aplicaciones locales."""
    print("\n=== ELIMINANDO ARCHIVOS DE MIGRACIÓN ===")
    
    for app in settings.INSTALLED_APPS:
        if app.startswith('django.') or app.startswith('rest_framework'):
            continue

        try:
            # Manejar aplicaciones en la carpeta 'apps'
            app_path = None
            
            try:
                # Primero intentar importar directamente
                app_path = Path(import_module(app).__file__).parent
            except ModuleNotFoundError:
                # Si falla, intentar con el prefijo 'apps.'
                try:
                    if not app.startswith('apps.'):
                        app_with_prefix = f'apps.{app}'
                        app_path = Path(import_module(app_with_prefix).__file__).parent
                except ModuleNotFoundError:
                    pass
                    
            if app_path is None:
                print(f"No se pudo encontrar la ruta para la aplicación {app}")
                continue
                
            migraciones_path = app_path / 'migrations'

            if migraciones_path.exists():
                print(f"Borrando migraciones en {app}")
                # Eliminar todos los archivos excepto __init__.py
                for archivo in migraciones_path.glob('*.py'):
                    if archivo.name != '__init__.py':
                        archivo.unlink()
                
                # Si no existe __init__.py, crearlo
                init_file = migraciones_path / '__init__.py'
                if not init_file.exists():
                    with open(init_file, 'w'):
                        pass
            else:
                # Crear el directorio de migraciones si no existe
                os.makedirs(migraciones_path)
                with open(migraciones_path / '__init__.py', 'w'):
                    pass
                print(f"Creado directorio de migraciones para {app}")
                
        except Exception as e:
            print(f"Error al eliminar migraciones para {app}: {e}")

def reiniciar_base_de_datos():
    """Elimina y recrea la base de datos, y aplica las migraciones iniciales."""
    print("\n=== REINICIANDO BASE DE DATOS ===")
    
    # Borrar la base de datos existente
    db_path = BASE_DIR / 'db.sqlite3'  # Ajustar según configuración
    if db_path.exists():
        print(f"Borrando la base de datos en {db_path}")
        os.remove(db_path)
    
    # Crear nuevas migraciones
    print("Creando nuevas migraciones...")
    call_command('makemigrations')
    
    # Aplicar migraciones a la nueva base de datos
    print("Aplicando migraciones a la nueva base de datos...")
    call_command('migrate')

def cargar_datos_iniciales():
    """Ejecuta los comandos de carga de datos iniciales."""
    print("\n=== CARGANDO DATOS INICIALES ===")
    
    try:
        print("Ejecutando: python manage.py load_initials")
        call_command('load_initials')
        
        print("Ejecutando: python manage.py load_puc --level all")
        call_command('load_puc', level='all')
        
        print("Ejecutando: python manage.py Crear_Menu")
        call_command('Crear_Menu')
    except Exception as e:
        print(f"Error al cargar datos iniciales: {e}")

def ejecutar_utils():
    """Ejecutar las inicializaciones de datos para todas las aplicaciones locales."""
    print("\n=== EJECUTANDO UTILIDADES DE INICIALIZACIÓN ===")
    
    for app in settings.INSTALLED_APPS:
        if app.startswith('django.') or app.startswith('rest_framework'):
            continue

        try:
            # Determinar el nombre correcto del módulo para importar
            module_name = app
            app_name = app.split('.')[-1].lower()
            
            # Intentar diferentes formas de importar el módulo utils
            utils_module = None
            possible_module_paths = [
                f'{app}.utils',         # apps.myapp.utils
                f'apps.{app}.utils'     # si app está registrado sin el prefijo 'apps.'
            ]
            
            for module_path in possible_module_paths:
                try:
                    utils_module = import_module(module_path)
                    break
                except ModuleNotFoundError:
                    continue
            
            if utils_module is None:
                print(f"No se encontró el módulo 'utils' en {app}")
                continue
                
            # Buscar la función 'datos_iniciales_<app>'
            func_name = f'datos_iniciales_{app_name}'
            if hasattr(utils_module, func_name):
                init_function = getattr(utils_module, func_name)
                print(f"Ejecutando {func_name} en {app}")
                init_function()
            else:
                print(f"No se encontró la función {func_name} en {app}")
        except Exception as e:
            print(f"Error ejecutando utilidades para {app}: {e}")

def mostrar_ayuda():
    """Muestra la ayuda del script."""
    print("""
    Script de reinicio y carga inicial del proyecto
    
    Uso:
        python ResetAndInitialize.py [opciones]
        
    Opciones:
        --help          Muestra esta ayuda
        --reset         Elimina migraciones y reinicia la base de datos
        --load          Carga datos iniciales (load_initials, load_puc, Crear_Menu)
        --utils         Ejecuta las funciones de utils de cada aplicación
        --all           Ejecuta todo el proceso (reset + load + utils)
        
    Si no se especifica ninguna opción, se ejecutará --all por defecto.
    """)

if __name__ == "__main__":
    # Procesar argumentos de línea de comandos
    args = sys.argv[1:]
    
    if not args or '--all' in args:
        do_reset = True
        do_load = True
        do_utils = True
    else:
        do_reset = '--reset' in args
        do_load = '--load' in args
        do_utils = '--utils' in args
        
        if '--help' in args:
            mostrar_ayuda()
            sys.exit(0)
    
    # Ejecutar las operaciones seleccionadas
    if do_reset:
        borrar_migraciones()
        reiniciar_base_de_datos()
        
    if do_load:
        cargar_datos_iniciales()
        
    if do_utils:
        ejecutar_utils()
        
    print("\n¡Proceso completado exitosamente!")