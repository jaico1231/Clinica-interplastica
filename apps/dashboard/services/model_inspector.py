from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Count, Sum, Avg, Min, Max, F, Q
from django.utils.translation import gettext as _
import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ModelInspector:
    """
    Clase para inspeccionar modelos y extraer información sobre ellos
    Permite obtener modelos, campos, relaciones y datos para análisis
    """
    
    # Lista de modelos de auditoría para monitoreo prioritario
    AUDIT_MODELS = settings.AUDIT_MODELS
    
    # Mapeo de tipos de campo a tipos de gráficos recomendados
    FIELD_TYPE_CHART_MAPPING = {
        'CharField': ['pie', 'bar', 'horizontal-bar'],
        'TextField': ['wordcloud'],
        'IntegerField': ['bar', 'line', 'scatter'],
        'FloatField': ['bar', 'line', 'scatter'],
        'DecimalField': ['bar', 'line', 'scatter'],
        'BooleanField': ['pie', 'bar'],
        'DateField': ['line', 'bar', 'calendar-heatmap'],
        'DateTimeField': ['line', 'time-series'],
        'ForeignKey': ['bar', 'pie', 'scatter'],
        'ManyToManyField': ['network', 'bar'],
        'OneToOneField': ['bar', 'pie'],
    }
    
    def get_all_models(self):
        """Obtiene todos los modelos registrados en el proyecto"""
        all_models = []
        
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                model_path = f"{model._meta.app_label}.{model._meta.model_name}"
                is_audit_model = model_path in self.AUDIT_MODELS
                
                all_models.append({
                    'app_label': model._meta.app_label,
                    'model_name': model._meta.model_name,
                    'verbose_name': model._meta.verbose_name,
                    'model_path': model_path,
                    'is_audit_model': is_audit_model,
                    'object_count': model.objects.count(),
                    'content_type_id': ContentType.objects.get_for_model(model).id
                })
        
        # Ordenar modelos: primero los de auditoría, luego por app_label y model_name
        all_models.sort(key=lambda x: (not x['is_audit_model'], x['app_label'], x['model_name']))
        
        return all_models
    
    def get_model_fields(self, app_label, model_name):
        """Obtiene todos los campos de un modelo específico"""
        try:
            model = apps.get_model(app_label, model_name)
            fields = []
            
            for field in model._meta.get_fields():
                # Ignorar campos de relación muchos a muchos o uno a muchos
                if field.many_to_many and not field.concrete:
                    continue
                
                # Si es una relación, obtener información adicional
                related_model = None
                if hasattr(field, 'related_model') and field.related_model:
                    related_model = {
                        'app_label': field.related_model._meta.app_label,
                        'model_name': field.related_model._meta.model_name,
                        'verbose_name': field.related_model._meta.verbose_name
                    }
                
                field_type = field.get_internal_type() if hasattr(field, 'get_internal_type') else type(field).__name__
                
                fields.append({
                    'name': field.name,
                    'verbose_name': getattr(field, 'verbose_name', field.name),
                    'field_type': field_type,
                    'is_relation': field.is_relation,
                    'related_model': related_model,
                    'is_primary_key': getattr(field, 'primary_key', False),
                    'is_unique': getattr(field, 'unique', False),
                    'is_null': getattr(field, 'null', False),
                    'recommended_chart_types': self.FIELD_TYPE_CHART_MAPPING.get(field_type, ['bar'])
                })
            
            return fields
            
        except Exception as e:
            logger.error(f"Error obteniendo campos para {app_label}.{model_name}: {str(e)}")
            return []
    
    def get_model_stats(self, app_label, model_name):
        """Obtiene estadísticas básicas de un modelo"""
        try:
            model = apps.get_model(app_label, model_name)
            total_objects = model.objects.count()
            
            stats = {
                'total_objects': total_objects,
                'fields_with_null': [],
                'date_range': {}
            }
            
            # Si no hay objetos, retornar estadísticas básicas
            if total_objects == 0:
                return stats
            
            # Analizar campos con valores nulos
            for field in model._meta.fields:
                if field.null:
                    null_count = model.objects.filter(**{f'{field.name}__isnull': True}).count()
                    stats['fields_with_null'].append({
                        'field_name': field.name,
                        'null_count': null_count,
                        'null_percentage': (null_count / total_objects) * 100
                    })
            
            # Estadísticas de campos de fecha
            for field in model._meta.fields:
                if isinstance(field, (models.DateField, models.DateTimeField)):
                    try:
                        min_date = model.objects.aggregate(Min(field.name))[f'{field.name}__min']
                        max_date = model.objects.aggregate(Max(field.name))[f'{field.name}__max']
                        if min_date and max_date:
                            stats['date_range'][field.name] = {
                                'min_date': min_date,
                                'max_date': max_date,
                                'span_days': (max_date.date() - min_date.date()).days if isinstance(max_date, datetime.datetime) else (max_date - min_date).days
                            }
                    except Exception as e:
                        logger.error(f"Error obteniendo rango de fechas para {field.name}: {str(e)}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas para {app_label}.{model_name}: {str(e)}")
            return {'error': str(e)}
    
    def get_field_value_distribution(self, app_label, model_name, field_name, limit=20):
        """Obtiene la distribución de valores para un campo específico"""
        try:
            model = apps.get_model(app_label, model_name)
            field = model._meta.get_field(field_name)
            
            # Para campos de relación, usar el id del objeto relacionado
            lookup_field = f"{field_name}_id" if field.is_relation else field_name
            
            # Agrupar por el campo y contar
            queryset = model.objects.values(lookup_field).annotate(count=Count('id')).order_by('-count')
            
            # Limitar resultados
            distribution = list(queryset[:limit])
            
            # Para campos relacionales, obtener información adicional
            if field.is_relation:
                related_model = field.related_model
                id_to_str = {}
                
                # Obtener los IDs de los objetos relacionados
                ids = [item[lookup_field] for item in distribution if item[lookup_field] is not None]
                
                if ids:
                    # Obtener los objetos relacionados
                    related_objects = related_model.objects.filter(pk__in=ids)
                    
                    # Mapear IDs a representaciones de cadena
                    for obj in related_objects:
                        id_to_str[obj.pk] = str(obj)
                    
                    # Reemplazar IDs con representaciones de cadena
                    for item in distribution:
                        if item[lookup_field] in id_to_str:
                            item['value_str'] = id_to_str[item[lookup_field]]
                        else:
                            item['value_str'] = f"ID: {item[lookup_field]}"
            
            # Para campos normales, agregar representación de cadena
            else:
                for item in distribution:
                    item['value_str'] = str(item[lookup_field])
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error obteniendo distribución para {app_label}.{model_name}.{field_name}: {str(e)}")
            return []
    
    def get_relation_data(self, app_label, model_name):
        """Obtiene datos de relaciones para el modelo"""
        try:
            model = apps.get_model(app_label, model_name)
            relations = {
                'foreign_keys': [],
                'reverse_relations': [],
                'many_to_many': []
            }
            
            # Obtener relaciones directas (ForeignKey, OneToOneField)
            for field in model._meta.fields:
                if field.is_relation:
                    relations['foreign_keys'].append({
                        'field_name': field.name,
                        'related_model': f"{field.related_model._meta.app_label}.{field.related_model._meta.model_name}",
                        'related_verbose_name': field.related_model._meta.verbose_name,
                        'field_type': field.get_internal_type()
                    })
            
            # Obtener relaciones many-to-many
            for field in model._meta.many_to_many:
                relations['many_to_many'].append({
                    'field_name': field.name,
                    'related_model': f"{field.related_model._meta.app_label}.{field.related_model._meta.model_name}",
                    'related_verbose_name': field.related_model._meta.verbose_name,
                    'field_type': field.get_internal_type()
                })
            
            # Obtener relaciones inversas
            for relation in model._meta.get_fields():
                if relation.is_relation and not relation.concrete and (relation.one_to_many or relation.one_to_one):
                    related_model = relation.related_model
                    relations['reverse_relations'].append({
                        'field_name': relation.name,
                        'related_model': f"{related_model._meta.app_label}.{related_model._meta.model_name}",
                        'related_verbose_name': related_model._meta.verbose_name,
                        'relation_type': 'one_to_many' if relation.one_to_many else 'one_to_one'
                    })
            
            return relations
            
        except Exception as e:
            logger.error(f"Error obteniendo relaciones para {app_label}.{model_name}: {str(e)}")
            return {'error': str(e)}
    
    def get_time_series_data(self, app_label, model_name, date_field, interval='month', value_field=None, aggregate='count'):
        """
        Obtiene datos de series temporales para un modelo
        
        Args:
            app_label: Etiqueta de la aplicación
            model_name: Nombre del modelo
            date_field: Campo de fecha para agrupar
            interval: Intervalo de tiempo (day, week, month, year)
            value_field: Campo para agregar (opcional)
            aggregate: Tipo de agregación (count, sum, avg, min, max)
        
        Returns:
            Lista de datos agrupados por tiempo
        """
        try:
            model = apps.get_model(app_label, model_name)
            
            # Crear truncamiento de fecha según el intervalo
            if interval == 'day':
                trunc_func = models.functions.TruncDay(date_field)
            elif interval == 'week':
                trunc_func = models.functions.TruncWeek(date_field)
            elif interval == 'month':
                trunc_func = models.functions.TruncMonth(date_field)
            elif interval == 'quarter':
                trunc_func = models.functions.TruncQuarter(date_field)
            elif interval == 'year':
                trunc_func = models.functions.TruncYear(date_field)
            else:
                trunc_func = models.functions.TruncMonth(date_field)
            
            # Base de la consulta
            queryset = model.objects.annotate(period=trunc_func).values('period')
            
            # Aplicar la agregación según el tipo
            if aggregate == 'count' or not value_field:
                queryset = queryset.annotate(value=Count('id'))
            elif aggregate == 'sum':
                queryset = queryset.annotate(value=Sum(value_field))
            elif aggregate == 'avg':
                queryset = queryset.annotate(value=Avg(value_field))
            elif aggregate == 'min':
                queryset = queryset.annotate(value=Min(value_field))
            elif aggregate == 'max':
                queryset = queryset.annotate(value=Max(value_field))
            
            # Ordenar por período
            queryset = queryset.order_by('period')
            
            # Convertir a formato adecuado para gráficos
            result = []
            for item in queryset:
                if item['period'] is not None:
                    result.append({
                        'period': item['period'].isoformat() if hasattr(item['period'], 'isoformat') else item['period'],
                        'value': item['value'] if item['value'] is not None else 0
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de series temporales para {app_label}.{model_name}.{date_field}: {str(e)}")
            return []
    
    def suggest_charts(self, app_label, model_name):
        """Sugiere gráficos que podrían ser útiles para el modelo"""
        try:
            model = apps.get_model(app_label, model_name)
            suggestions = []
            
            # Obtener campos del modelo
            fields = self.get_model_fields(app_label, model_name)
            
            # Buscar campos de fecha para series temporales
            date_fields = [f for f in fields if f['field_type'] in ('DateField', 'DateTimeField')]
            
            if date_fields:
                for date_field in date_fields:
                    suggestions.append({
                        'title': f'Evolución temporal por {date_field["verbose_name"]}',
                        'chart_type': 'line',
                        'description': f'Muestra la evolución del número de registros a lo largo del tiempo según {date_field["verbose_name"]}',
                        'config': {
                            'x_axis_field': date_field['name'],
                            'y_axis_field': 'count',
                            'interval': 'month',
                            'aggregate': 'count'
                        }
                    })
            
            # Buscar campos categóricos para gráficos de distribución
            categorical_fields = [f for f in fields if f['field_type'] in ('CharField', 'BooleanField') or 
                                (f['is_relation'] and f['field_type'] in ('ForeignKey', 'ManyToManyField'))]
            
            for field in categorical_fields:
                chart_type = 'pie' if field['field_type'] in ('BooleanField', 'CharField') and field['recommended_chart_types'][0] == 'pie' else 'bar'
                
                suggestions.append({
                    'title': f'Distribución por {field["verbose_name"]}',
                    'chart_type': chart_type,
                    'description': f'Muestra la distribución de registros según {field["verbose_name"]}',
                    'config': {
                        'x_axis_field': field['name'],
                        'y_axis_field': 'count',
                        'aggregate': 'count'
                    }
                })
            
            # Buscar campos numéricos para estadísticas
            numeric_fields = [f for f in fields if f['field_type'] in ('IntegerField', 'FloatField', 'DecimalField')]
            
            if numeric_fields and categorical_fields:
                for num_field in numeric_fields[:3]:  # Limitar a 3 sugerencias
                    for cat_field in categorical_fields[:2]:  # Limitar a 2 categorías por campo numérico
                        suggestions.append({
                            'title': f'{num_field["verbose_name"]} por {cat_field["verbose_name"]}',
                            'chart_type': 'bar',
                            'description': f'Muestra {num_field["verbose_name"]} agrupado por {cat_field["verbose_name"]}',
                            'config': {
                                'x_axis_field': cat_field['name'],
                                'y_axis_field': num_field['name'],
                                'aggregate': 'sum'
                            }
                        })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generando sugerencias para {app_label}.{model_name}: {str(e)}")
            return []
