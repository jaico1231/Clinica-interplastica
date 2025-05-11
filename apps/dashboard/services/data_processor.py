from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Sum, Avg, Min, Max, F, Q, QuerySet
from django.db.models.functions import Trunc
from django.utils import timezone
import datetime
import json
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Clase para procesar datos de modelos y generar información para gráficos
    Permite agregar, filtrar y transformar datos para visualización
    """
    
    AGGREGATION_FUNCTIONS = {
        'count': Count('id'),
        'sum': Sum,
        'avg': Avg,
        'min': Min,
        'max': Max,
    }
    
    DATE_INTERVALS = {
        'day': 'TruncDay',
        'week': 'TruncWeek',
        'month': 'TruncMonth',
        'quarter': 'TruncQuarter',
        'year': 'TruncYear',
    }
    
    def get_model_from_content_type(self, content_type_id):
        """Obtiene un modelo a partir de su ID de ContentType"""
        try:
            content_type = ContentType.objects.get(id=content_type_id)
            return apps.get_model(content_type.app_label, content_type.model)
        except ContentType.DoesNotExist:
            logger.error(f"ContentType con ID {content_type_id} no existe")
            return None
        except Exception as e:
            logger.error(f"Error obteniendo modelo para ContentType {content_type_id}: {str(e)}")
            return None
    
    def apply_filters(self, queryset, filter_config):
        """Aplica filtros a un queryset según la configuración"""
        if not filter_config:
            return queryset
        
        try:
            for filter_item in filter_config:
                field = filter_item.get('field')
                operator = filter_item.get('operator', 'exact')
                value = filter_item.get('value')
                
                if not field or value is None:
                    continue
                
                # Construir el lookup para el filtro
                lookup = f"{field}__{operator}"
                
                # Aplicar el filtro
                if operator == 'in':
                    if isinstance(value, str):
                        value = json.loads(value)
                    queryset = queryset.filter(**{lookup: value})
                elif operator == 'range':
                    if isinstance(value, str):
                        value = json.loads(value)
                    if len(value) == 2:
                        queryset = queryset.filter(**{lookup: value})
                elif operator == 'isnull':
                    queryset = queryset.filter(**{lookup: bool(value)})
                else:
                    queryset = queryset.filter(**{lookup: value})
            
            return queryset
        except Exception as e:
            logger.error(f"Error aplicando filtros: {str(e)}")
            return queryset
    
    def apply_date_range(self, queryset, date_field, start_date=None, end_date=None):
        """Aplica filtros de rango de fechas a un queryset"""
        if not date_field:
            return queryset
        
        filters = {}
        
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            filters[f"{date_field}__gte"] = start_date
        
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            filters[f"{date_field}__lte"] = end_date
        
        if filters:
            return queryset.filter(**filters)
        return queryset
    
    def get_chart_data(self, saved_chart):
        """Obtiene los datos para un gráfico guardado"""
        try:
            model = self.get_model_from_content_type(saved_chart.model_content_type.id)
            if not model:
                return {'error': 'Modelo no encontrado'}
            
            # Obtener la configuración del gráfico
            x_axis_field = saved_chart.x_axis_field
            y_axis_field = saved_chart.y_axis_field
            filter_config = saved_chart.filter_config or {}
            chart_config = saved_chart.chart_config or {}
            
            # Valores predeterminados
            aggregate_func = chart_config.get('aggregate', 'count')
            group_by = chart_config.get('group_by', None)
            date_interval = chart_config.get('date_interval', 'month')
            limit = chart_config.get('limit', 50)
            
            # Iniciar con todos los objetos del modelo
            queryset = model.objects.all()
            
            # Aplicar filtros
            queryset = self.apply_filters(queryset, filter_config)
            
            # Determinar si el campo X es una fecha
            is_date_field = False
            try:
                field = model._meta.get_field(x_axis_field)
                is_date_field = field.get_internal_type() in ('DateField', 'DateTimeField')
            except:
                pass
            
            # Procesar datos según el tipo de gráfico
            chart_type = saved_chart.chart_type.code
            
            # Para gráficos de series de tiempo
            if is_date_field and chart_type in ['line', 'area', 'time-series']:
                return self.process_time_series_data(
                    queryset=queryset,
                    model=model,
                    x_field=x_axis_field,
                    y_field=y_axis_field,
                    interval=date_interval,
                    aggregate_func=aggregate_func,
                    group_by=group_by
                )
            
            # Para gráficos de distribución (pie, bar, etc.)
            elif chart_type in ['pie', 'bar', 'horizontal-bar', 'donut']:
                return self.process_distribution_data(
                    queryset=queryset,
                    model=model,
                    x_field=x_axis_field,
                    y_field=y_axis_field,
                    aggregate_func=aggregate_func,
                    limit=limit,
                    group_by=group_by
                )
            
            # Para gráficos de dispersión
            elif chart_type == 'scatter':
                return self.process_scatter_data(
                    queryset=queryset,
                    model=model,
                    x_field=x_axis_field,
                    y_field=y_axis_field,
                    group_by=group_by
                )
            
            # Para otros tipos de gráficos
            else:
                return self.process_generic_data(
                    queryset=queryset,
                    model=model,
                    x_field=x_axis_field,
                    y_field=y_axis_field,
                    aggregate_func=aggregate_func,
                    limit=limit
                )
                
        except Exception as e:
            logger.error(f"Error obteniendo datos para gráfico {saved_chart.id}: {str(e)}")
            return {'error': str(e)}
    
    def process_time_series_data(self, queryset, model, x_field, y_field, interval='month', aggregate_func='count', group_by=None):
        """Procesa datos para series de tiempo"""
        try:
            # Obtener la función de truncamiento según el intervalo
            trunc_function_name = self.DATE_INTERVALS.get(interval, 'TruncMonth')
            trunc_function = getattr(Trunc, trunc_function_name.replace('Trunc', '').lower(), 'month')
            
            # Anotar con el período truncado
            queryset = queryset.annotate(period=Trunc(x_field, trunc_function))
            
            # Agrupar por período y opcionalmente por otro campo
            group_fields = ['period']
            if group_by:
                group_fields.append(group_by)
            
            # Agregar campos de agrupación a values()
            queryset = queryset.values(*group_fields)
            
            # Aplicar la función de agregación
            if aggregate_func == 'count':
                queryset = queryset.annotate(value=Count('id'))
            elif y_field != 'count':
                agg_func = self.AGGREGATION_FUNCTIONS.get(aggregate_func, Count('id'))
                if aggregate_func != 'count':
                    agg_func = agg_func(y_field)
                queryset = queryset.annotate(value=agg_func)
            
            # Ordenar por período
            queryset = queryset.order_by('period')
            
            # Formatear los resultados
            results = []
            for item in queryset:
                result_item = {
                    'period': item['period'].isoformat() if hasattr(item['period'], 'isoformat') else str(item['period']),
                    'value': float(item['value']) if item['value'] is not None else 0
                }
                
                # Agregar campo de agrupación si existe
                if group_by and group_by in item:
                    result_item['group'] = str(item[group_by])
                
                results.append(result_item)
            
            return results
            
        except Exception as e:
            logger.error(f"Error procesando datos de series temporales: {str(e)}")
            return {'error': str(e)}
    
    def process_distribution_data(self, queryset, model, x_field, y_field, aggregate_func='count', limit=50, group_by=None):
        """Procesa datos para gráficos de distribución"""
        try:
            # Determinar si el campo X es una relación
            is_relation = False
            relation_model = None
            
            try:
                field = model._meta.get_field(x_field)
                is_relation = field.is_relation
                if is_relation:
                    relation_model = field.related_model
            except:
                pass
            
            # Campos para agrupar
            group_fields = [x_field]
            if group_by and group_by != x_field:
                group_fields.append(group_by)
            
            # Agrupar por los campos seleccionados
            queryset = queryset.values(*group_fields)
            
            # Aplicar la función de agregación
            if aggregate_func == 'count' or y_field == 'count':
                queryset = queryset.annotate(value=Count('id'))
            else:
                agg_func = self.AGGREGATION_FUNCTIONS.get(aggregate_func, Count('id'))
                if aggregate_func != 'count':
                    agg_func = agg_func(y_field)
                queryset = queryset.annotate(value=agg_func)
            
            # Ordenar y limitar
            queryset = queryset.order_by('-value')[:limit]
            
            # Formatear los resultados
            results = []
            for item in queryset:
                x_value = item[x_field]
                
                # Convertir a formato legible
                if x_value is None:
                    label = 'Sin valor'
                elif is_relation and relation_model and x_value:
                    try:
                        related_obj = relation_model.objects.get(pk=x_value)
                        label = str(related_obj)
                    except:
                        label = f'ID: {x_value}'
                else:
                    label = str(x_value)
                
                result_item = {
                    'label': label,
                    'value': float(item['value']) if item['value'] is not None else 0,
                    'raw_value': x_value
                }
                
                # Agregar campo de agrupación si existe
                if group_by and group_by in item and group_by != x_field:
                    result_item['group'] = str(item[group_by])
                
                results.append(result_item)
            
            return results
            
        except Exception as e:
            logger.error(f"Error procesando datos de distribución: {str(e)}")
            return {'error': str(e)}
    
    def process_scatter_data(self, queryset, model, x_field, y_field, group_by=None):
        """Procesa datos para gráficos de dispersión"""
        try:
            # Campos para seleccionar
            select_fields = [x_field, y_field]
            if group_by:
                select_fields.append(group_by)
            
            # Obtener valores
            data = list(queryset.values(*select_fields))
            
            # Formatear los resultados
            results = []
            for item in data:
                x_value = item.get(x_field)
                y_value = item.get(y_field)
                
                # Ignorar registros sin valores
                if x_value is None or y_value is None:
                    continue
                
                result_item = {
                    'x': float(x_value) if isinstance(x_value, (int, float)) else str(x_value),
                    'y': float(y_value) if isinstance(y_value, (int, float)) else str(y_value),
                }
                
                # Agregar campo de agrupación si existe
                if group_by and group_by in item:
                    result_item['group'] = str(item[group_by])
                
                results.append(result_item)
            
            return results
            
        except Exception as e:
            logger.error(f"Error procesando datos de dispersión: {str(e)}")
            return {'error': str(e)}
    
    def process_generic_data(self, queryset, model, x_field, y_field, aggregate_func='count', limit=50):
        """Procesa datos para otros tipos de gráficos"""
        try:
            # Agrupar por el campo X
            queryset = queryset.values(x_field)
            
            # Aplicar la función de agregación
            if aggregate_func == 'count' or y_field == 'count':
                queryset = queryset.annotate(value=Count('id'))
            else:
                agg_func = self.AGGREGATION_FUNCTIONS.get(aggregate_func, Count('id'))
                if aggregate_func != 'count':
                    agg_func = agg_func(y_field)
                queryset = queryset.annotate(value=agg_func)
            
            # Ordenar y limitar
            queryset = queryset.order_by('-value')[:limit]
            
            # Formatear los resultados
            results = []
            for item in queryset:
                x_value = item[x_field]
                value = item['value']
                
                results.append({
                    'label': str(x_value) if x_value is not None else 'Sin valor',
                    'value': float(value) if value is not None else 0,
                    'raw_value': x_value
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error procesando datos genéricos: {str(e)}")
            return {'error': str(e)}
    
    def generate_report(self, data_report):
        """Genera un informe según la configuración del informe"""
        try:
            report_config = data_report.report_config or {}
            models_included = data_report.models_included or []
            
            # Objeto de respuesta
            response = {
                'report_id': data_report.id,
                'title': data_report.title,
                'generated_at': timezone.now().isoformat(),
                'models_data': [],
                'summary': {}
            }
            
            # Procesar cada modelo incluido
            for model_info in models_included:
                app_label = model_info.get('app_label')
                model_name = model_info.get('model_name')
                fields = model_info.get('fields', [])
                filters = model_info.get('filters', [])
                
                if not app_label or not model_name:
                    continue
                
                try:
                    # Obtener el modelo
                    model = apps.get_model(app_label, model_name)
                    
                    # Iniciar con todos los objetos
                    queryset = model.objects.all()
                    
                    # Aplicar filtros
                    queryset = self.apply_filters(queryset, filters)
                    
                    # Obtener conteo y metadatos
                    count = queryset.count()
                    
                    # Procesar campos seleccionados
                    field_data = []
                    for field_name in fields:
                        try:
                            field = model._meta.get_field(field_name)
                            field_type = field.get_internal_type()
                            
                            # Estadísticas específicas por tipo de campo
                            stats = {}
                            
                            if field_type in ('IntegerField', 'FloatField', 'DecimalField'):
                                # Estadísticas numéricas
                                stats = queryset.aggregate(
                                    min=Min(field_name),
                                    max=Max(field_name),
                                    avg=Avg(field_name),
                                    sum=Sum(field_name)
                                )
                            
                            elif field_type in ('DateField', 'DateTimeField'):
                                # Estadísticas de fecha
                                date_stats = queryset.aggregate(
                                    min_date=Min(field_name),
                                    max_date=Max(field_name)
                                )
                                
                                if date_stats['min_date'] and date_stats['max_date']:
                                    min_date = date_stats['min_date']
                                    max_date = date_stats['max_date']
                                    
                                    stats = {
                                        'min_date': min_date.isoformat() if hasattr(min_date, 'isoformat') else str(min_date),
                                        'max_date': max_date.isoformat() if hasattr(max_date, 'isoformat') else str(max_date),
                                    }
                                    
                                    # Calcular duración en días
                                    if isinstance(min_date, datetime.datetime) and isinstance(max_date, datetime.datetime):
                                        stats['duration_days'] = (max_date.date() - min_date.date()).days
                                    elif isinstance(min_date, datetime.date) and isinstance(max_date, datetime.date):
                                        stats['duration_days'] = (max_date - min_date).days
                            
                            elif field_type in ('CharField', 'TextField'):
                                # Estadísticas de texto
                                null_count = queryset.filter(**{f"{field_name}__isnull": True}).count()
                                blank_count = queryset.filter(**{f"{field_name}__exact": ""}).count()
                                
                                stats = {
                                    'null_count': null_count,
                                    'blank_count': blank_count,
                                    'populated_count': count - null_count - blank_count
                                }
                            
                            # Agregar información del campo
                            field_data.append({
                                'name': field_name,
                                'verbose_name': getattr(field, 'verbose_name', field_name),
                                'type': field_type,
                                'stats': stats
                            })
                            
                        except Exception as field_error:
                            logger.error(f"Error procesando campo {field_name}: {str(field_error)}")
                            field_data.append({
                                'name': field_name,
                                'error': str(field_error)
                            })
                    
                    # Agregar datos del modelo al informe
                    response['models_data'].append({
                        'app_label': app_label,
                        'model_name': model_name,
                        'verbose_name': model._meta.verbose_name,
                        'count': count,
                        'fields': field_data
                    })
                    
                except Exception as model_error:
                    logger.error(f"Error procesando modelo {app_label}.{model_name}: {str(model_error)}")
                    response['models_data'].append({
                        'app_label': app_label,
                        'model_name': model_name,
                        'error': str(model_error)
                    })
            
            # Generar resumen del informe
            response['summary'] = {
                'total_models': len(response['models_data']),
                'models_with_data': sum(1 for m in response['models_data'] if 'count' in m and m['count'] > 0),
                'total_records': sum(m.get('count', 0) for m in response['models_data'] if 'count' in m)
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error generando informe {data_report.id}: {str(e)}")
            return {'error': str(e)}