from django.db import transaction
from django.utils.translation import gettext_lazy as _
import os
import logging

logger = logging.getLogger(__name__)

def load_question_types():
    """
    Carga los tipos de preguntas predefinidos en la base de datos.
    Esta función se puede llamar desde diferentes partes de la aplicación.
    """
    try:
        from apps.surveys.models.surveymodel import QuestionType
        
        with transaction.atomic():
            default_types = QuestionType.get_default_types()
            created_count = 0
            
            for type_data in default_types:
                _, created = QuestionType.objects.get_or_create(
                    name=type_data['name'],
                    defaults={'description': type_data['description']}
                )
                if created:
                    created_count += 1
            
            return {
                'success': True,
                'created': created_count,
                'total': len(default_types),
                'message': f'Se cargaron {created_count} tipos de preguntas de un total de {len(default_types)}'
            }
    
    except Exception as e:
        logger.error(f"Error al cargar tipos de preguntas: {e}")
        return {
            'success': False,
            'message': f'Error al cargar tipos de preguntas: {e}'
        }

def create_initial_data_file():
    """
    Crea un archivo indicador para señalar que se deben cargar datos iniciales.
    Este archivo será verificado y eliminado después de la carga.
    """
    try:
        from django.conf import settings
        
        initial_data_path = os.path.join(settings.BASE_DIR, 'apps', 'surveys', 'initial_data')
        
        with open(initial_data_path, 'w') as f:
            f.write('Este archivo indica que se deben cargar datos iniciales al iniciar la aplicación.')
        
        return {
            'success': True,
            'message': f'Archivo de datos iniciales creado en {initial_data_path}',
            'path': initial_data_path
        }
    
    except Exception as e:
        logger.error(f"Error al crear archivo de datos iniciales: {e}")
        return {
            'success': False,
            'message': f'Error al crear archivo de datos iniciales: {e}'
        }

def load_all_initial_data():
    """
    Función principal para cargar todos los datos iniciales del módulo de encuestas.
    Esta función se puede llamar desde scripts de migración, señales, o comandos de gestión.
    """
    print("Iniciando carga de datos iniciales del módulo de encuestas...")
    
    # Registro de resultados para cada tipo de datos
    results = {}
    
    # Cargar tipos de preguntas
    results['question_types'] = load_question_types()
    
    # Aquí se pueden agregar más funciones para cargar otros tipos de datos iniciales
    # results['otro_tipo_datos'] = load_otro_tipo_datos()
    
    # Registrar resultados
    for data_type, result in results.items():
        if result['success']:
            print(f"✅ {data_type}: {result['message']}")
        else:
            print(f"❌ {data_type}: {result['message']}")
    
    return results

# Función para verificar datos desde el archivo apps.py
def check_initial_data():
    """
    Verifica si existe el archivo de datos iniciales y los carga si es necesario.
    Esta función se puede llamar desde apps.py para cargar datos al iniciar la aplicación.
    """
    try:
        from django.conf import settings
        from apps.surveys.models.surveymodel import QuestionType
        
        initial_data_path = os.path.join(settings.BASE_DIR, 'apps', 'surveys', 'initial_data')
        
        # Verificar si existe el archivo o no hay tipos de preguntas
        if os.path.exists(initial_data_path) or QuestionType.objects.count() == 0:
            # Cargar datos iniciales
            results = load_all_initial_data()
            
            # Eliminar archivo si existe
            if os.path.exists(initial_data_path):
                os.remove(initial_data_path)
                print(f"✅ Archivo de datos iniciales eliminado: {initial_data_path}")
            
            return results
        
        return {'success': True, 'message': 'No fue necesario cargar datos iniciales'}
    
    except Exception as e:
        logger.error(f"Error al verificar datos iniciales: {e}")
        return {'success': False, 'message': f'Error al verificar datos iniciales: {e}'}