#!/usr/bin/env python
import os
import sys
import django
import traceback
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

def ejecutar_comandos_load():
    """Busca y ejecuta todos los comandos de management que empiezan con 'load_'."""
    print("\n=== EJECUTANDO COMANDOS DE CARGA DE DATOS ===")
    
    # Primero ejecutar comandos específicos que sabemos que son necesarios
    comandos_especificos = [
        {'name': 'load_initials', 'args': {}},
        {'name': 'load_puc', 'args': {'level': 'all'}},
        {'name': 'load_waste', 'args': {'level': 'all'}}
    ]
    
    print("Ejecutando comandos específicos prioritarios...")
    for comando in comandos_especificos:
        try:
            print(f"Ejecutando comando: {comando['name']} con argumentos: {comando['args']}")
            call_command(comando['name'], **comando['args'])
            print(f"✅ Comando {comando['name']} ejecutado con éxito")
        except Exception as e:
            print(f"❌ Error ejecutando {comando['name']}: {str(e)}")
            print("Detalles del error:")
            traceback.print_exc()
    
    # Luego buscar y ejecutar todos los demás comandos load_*
    print("\nBuscando otros comandos load_* en todas las aplicaciones...")
    
    for app in settings.INSTALLED_APPS:
        if app.startswith('django.') or app.startswith('rest_framework'):
            continue

        try:
            # Determinar el nombre correcto de la aplicación
            app_name = app.split('.')[-1]
            
            # Construir el path del módulo de comandos
            try:
                module = import_module(f'{app}.management')
                commands_path = Path(module.__file__).parent / 'commands'
                if not commands_path.exists():
                    continue
            except (ModuleNotFoundError, AttributeError):
                continue

            # Buscar comandos de carga (load_*)
            for command_file in commands_path.glob('*.py'):
                command_name = command_file.stem
                
                # Solo ejecutar comandos que empiecen con 'load_' y no sean los específicos ya ejecutados
                if (command_name.startswith('load_') and 
                    command_name != '__init__' and
                    command_name not in [cmd['name'] for cmd in comandos_especificos]):
                    
                    try:
                        print(f"Ejecutando comando: {command_name} de la app {app_name}")
                        # Intentar primero con --level all
                        try:
                            call_command(command_name, level='all')
                        except:
                            # Si falla con --level all, intentar sin argumentos
                            call_command(command_name)
                        print(f"✅ Comando {command_name} ejecutado con éxito")
                    except Exception as e:
                        print(f"❌ Error ejecutando {command_name}: {str(e)}")
                        print("Detalles del error:")
                        traceback.print_exc()
        
        except Exception as e:
            print(f"Error al procesar app {app}: {str(e)}")
            traceback.print_exc()

def ejecutar_comandos_crear():
    """Busca y ejecuta todos los comandos de management que empiezan con 'crear_' o 'Crear_'."""
    print("\n=== EJECUTANDO COMANDOS DE CREACIÓN ===")
    
    # Primero ejecutar Crear_Menu específicamente
    try:
        print("Ejecutando comando: Crear_Menu")
        call_command('Crear_Menu')
        print("✅ Comando Crear_Menu ejecutado con éxito")
    except Exception as e:
        print(f"❌ Error ejecutando Crear_Menu: {str(e)}")
        print("Detalles del error:")
        traceback.print_exc()
    
    # Luego buscar y ejecutar otros comandos de creación
    print("\nBuscando otros comandos crear_* o Crear_* en todas las aplicaciones...")
    
    for app in settings.INSTALLED_APPS:
        if app.startswith('django.') or app.startswith('rest_framework'):
            continue

        try:
            # Determinar el nombre correcto de la aplicación
            app_name = app.split('.')[-1]
            
            # Construir el path del módulo de comandos
            try:
                module = import_module(f'{app}.management')
                commands_path = Path(module.__file__).parent / 'commands'
                if not commands_path.exists():
                    continue
            except (ModuleNotFoundError, AttributeError):
                continue

            # Buscar comandos de creación (crear_* o Crear_*)
            for command_file in commands_path.glob('*.py'):
                command_name = command_file.stem
                
                # Solo ejecutar comandos que empiecen con 'crear_' o 'Crear_' y no sean 'Crear_Menu'
                if ((command_name.startswith('crear_') or command_name.startswith('Crear_')) and 
                    command_name != '__init__' and 
                    command_name != 'Crear_Menu'):
                    
                    try:
                        print(f"Ejecutando comando: {command_name} de la app {app_name}")
                        call_command(command_name)
                        print(f"✅ Comando {command_name} ejecutado con éxito")
                    except Exception as e:
                        print(f"❌ Error ejecutando {command_name}: {str(e)}")
                        print("Detalles del error:")
                        traceback.print_exc()
        
        except Exception as e:
            print(f"Error al procesar app {app}: {str(e)}")
            traceback.print_exc()

def mostrar_ayuda():
    """Muestra la ayuda del script."""
    print("""
    Script de reinicio y carga inicial del proyecto
    
    Uso:
        python ResetAndInitialize.py [opciones]
        
    Opciones:
        --help          Muestra esta ayuda
        --reset         Elimina migraciones y reinicia la base de datos
        --load          Ejecuta todos los comandos load_* de todas las apps
        --create        Ejecuta todos los comandos crear_* o Crear_* de todas las apps
        --all           Ejecuta todo el proceso (reset + load + create)
        
    Si no se especifica ninguna opción, se ejecutará --all por defecto.
    """)

if __name__ == "__main__":
    # Procesar argumentos de línea de comandos
    args = sys.argv[1:]
    
    if not args or '--all' in args:
        do_reset = True
        do_load = True
        do_create = True
    else:
        do_reset = '--reset' in args
        do_load = '--load' in args
        do_create = '--create' in args
        
        if '--help' in args:
            mostrar_ayuda()
            sys.exit(0)
    
    # Ejecutar las operaciones seleccionadas
    if do_reset:
        borrar_migraciones()
        reiniciar_base_de_datos()
        
    if do_load:
        ejecutar_comandos_load()
        
    if do_create:
        ejecutar_comandos_crear()
        
    print("\n¡Proceso completado exitosamente!")