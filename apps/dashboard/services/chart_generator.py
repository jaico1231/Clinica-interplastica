import json
import logging
from django.utils.translation import gettext as _
from apps.dashboard.services.data_processor import DataProcessor

logger = logging.getLogger(__name__)

class ChartGenerator:
    """
    Clase para generar configuraciones de gráficos para diferentes bibliotecas
    Permite generar configuraciones para Chart.js, Recharts, etc.
    """
    
    # Paletas de colores predefinidas
    COLOR_PALETTES = {
        'default': ['#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab'],
        'blue': ['#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600'],
        'green': ['#0d4b26', '#146c39', '#1a8d4c', '#1faf5e', '#24d171', '#4edc8c', '#79e6a7', '#a3f0c2'],
        'red': ['#7f0000', '#b30000', '#d40000', '#ff0000', '#ff4545', '#ff7a7a', '#ffafaf', '#ffe4e4'],
        'grayscale': ['#232323', '#454545', '#676767', '#898989', '#ababab', '#cdcdcd', '#efefef'],
    }
    
    # Tipos de gráficos soportados
    CHART_TYPES = {
        'bar': {
            'name': _('Barras'),
            'description': _('Gráfico de barras vertical'),
            'chartjs_type': 'bar',
            'recharts_component': 'BarChart',
        },
        'horizontal-bar': {
            'name': _('Barras horizontales'),
            'description': _('Gráfico de barras horizontal'),
            'chartjs_type': 'horizontalBar',
            'recharts_component': 'BarChart',
            'recharts_layout': 'horizontal',
        },
        'line': {
            'name': _('Líneas'),
            'description': _('Gráfico de líneas para datos temporales o continuos'),
            'chartjs_type': 'line',
            'recharts_component': 'LineChart',
        },
        'area': {
            'name': _('Área'),
            'description': _('Gráfico de área para datos temporales'),
            'chartjs_type': 'line',
            'chartjs_options': {'fill': True},
            'recharts_component': 'AreaChart',
        },
        'pie': {
            'name': _('Pastel'),
            'description': _('Gráfico circular para mostrar proporciones'),
            'chartjs_type': 'pie',
            'recharts_component': 'PieChart',
        },
        'donut': {
            'name': _('Dona'),
            'description': _('Gráfico tipo dona para mostrar proporciones'),
            'chartjs_type': 'doughnut',
            'recharts_component': 'PieChart',
            'recharts_options': {'innerRadius': '60%'},
        },
        'scatter': {
            'name': _('Dispersión'),
            'description': _('Gráfico de puntos para mostrar correlaciones'),
            'chartjs_type': 'scatter',
            'recharts_component': 'ScatterChart',
        },
        'radar': {
            'name': _('Radar'),
            'description': _('Gráfico de radar para comparar múltiples variables'),
            'chartjs_type': 'radar',
            'recharts_component': 'RadarChart',
        },
        'calendar-heatmap': {
            'name': _('Mapa de calor de calendario'),
            'description': _('Mapa de calor para visualizar datos en un calendario'),
            'recharts_component': 'CalendarHeatmap',
        }
    }
    
    def __init__(self):
        self.data_processor = DataProcessor()
    
    def ensure_dict(self, value, default=None):
        """
        Asegura que un valor sea un diccionario.
        Si es una cadena, intenta convertirla a diccionario.
        
        Args:
            value: El valor a convertir
            default: Valor por defecto si la conversión falla
            
        Returns:
            dict: El valor como diccionario
        """
        if default is None:
            default = {}
            
        if value is None:
            return default
            
        if isinstance(value, dict):
            return value
            
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"No se pudo parsear cadena JSON: {value[:50]}...")
                return default
                
        return default
    
    def generate_chart_config(self, saved_chart, format='chartjs'):
        """
        Genera la configuración para un gráfico guardado en el formato especificado
        
        Args:
            saved_chart: Objeto SavedChart con la configuración
            format: Formato de salida ('chartjs', 'recharts', 'highcharts')
        
        Returns:
            Configuración del gráfico en el formato solicitado
        """
        try:
            # Obtener datos para el gráfico
            chart_data = self.data_processor.get_chart_data(saved_chart)
            
            # Verificar si hay error en los datos
            if isinstance(chart_data, dict) and 'error' in chart_data:
                return {'error': chart_data['error']}
            
            # Obtener tipo de gráfico y asegurar que sea una cadena
            chart_type = str(saved_chart.chart_type.code)
            
            # Llamar al método específico según el formato solicitado
            if format == 'chartjs':
                return self.generate_chartjs_config(chart_type, chart_data, saved_chart)
            elif format == 'recharts':
                return self.generate_recharts_config(chart_type, chart_data, saved_chart)
            else:
                return {'error': f'Formato {format} no soportado'}
                
        except Exception as e:
            logger.error(f"Error generando configuración para gráfico {saved_chart.id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': str(e)}
    
    def generate_chartjs_config(self, chart_type, chart_data, saved_chart):
        """Genera configuración para Chart.js"""
        try:
            # Obtener información del tipo de gráfico
            chart_info = self.CHART_TYPES.get(chart_type, self.CHART_TYPES['bar'])
            
            # Verificar que chart_info sea un diccionario
            if not isinstance(chart_info, dict):
                logger.error(f"Tipo de gráfico no válido: {chart_type}")
                return {'error': f'Tipo de gráfico no válido: {chart_type}'}
            
            chartjs_type = chart_info.get('chartjs_type', 'bar')
            
            # Obtener esquema de colores
            color_scheme = saved_chart.color_scheme or 'default'
            colors = self.COLOR_PALETTES.get(color_scheme, self.COLOR_PALETTES['default'])
            
            # Asegurar que chart_config sea un diccionario
            chart_config = self.ensure_dict(saved_chart.chart_config)
            
            # Configuración básica
            config = {
                'type': chartjs_type,
                'data': {},
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': saved_chart.title,
                            'font': {
                                'size': 16
                            }
                        },
                        'tooltip': {
                            'enabled': True
                        },
                        'legend': {
                            'display': True,
                            'position': 'top'
                        }
                    }
                }
            }
            
            # Aplicar opciones específicas del tipo de gráfico
            if 'chartjs_options' in chart_info:
                chartjs_options = self.ensure_dict(chart_info.get('chartjs_options'))
                for key, value in chartjs_options.items():
                    if isinstance(value, dict):
                        if key not in config['options']:
                            config['options'][key] = {}
                        for sub_key, sub_value in value.items():
                            config['options'][key][sub_key] = sub_value
                    else:
                        config['options'][key] = value
            
            # Procesar datos según el tipo de gráfico
            if chart_type in ['pie', 'donut']:
                labels = [item['label'] for item in chart_data]
                values = [item['value'] for item in chart_data]
                
                config['data'] = {
                    'labels': labels,
                    'datasets': [{
                        'data': values,
                        'backgroundColor': colors[:len(values)],
                        'borderWidth': 1
                    }]
                }
                
            elif chart_type in ['bar', 'horizontal-bar']:
                labels = [item['label'] for item in chart_data]
                values = [item['value'] for item in chart_data]
                
                config['data'] = {
                    'labels': labels,
                    'datasets': [{
                        'label': saved_chart.y_axis_field,
                        'data': values,
                        'backgroundColor': colors[0],
                        'borderColor': colors[0],
                        'borderWidth': 1
                    }]
                }
                
                # Configuración específica para barras horizontales
                if chart_type == 'horizontal-bar':
                    config['options']['indexAxis'] = 'y'
                
            elif chart_type in ['line', 'area']:
                # Detectar si hay grupos
                has_groups = any('group' in item for item in chart_data)
                
                if has_groups:
                    # Agrupar datos por el campo de grupo
                    grouped_data = {}
                    all_periods = set()
                    
                    for item in chart_data:
                        period = item['period']
                        group = item.get('group', 'Sin grupo')
                        value = item['value']
                        
                        if group not in grouped_data:
                            grouped_data[group] = {}
                        
                        grouped_data[group][period] = value
                        all_periods.add(period)
                    
                    # Ordenar períodos
                    sorted_periods = sorted(all_periods)
                    
                    # Crear dataset para cada grupo
                    datasets = []
                    for i, (group, periods) in enumerate(grouped_data.items()):
                        color_index = i % len(colors)
                        
                        datasets.append({
                            'label': str(group),
                            'data': [periods.get(period, 0) for period in sorted_periods],
                            'borderColor': colors[color_index],
                            'backgroundColor': colors[color_index] if chart_type == 'area' else 'rgba(0,0,0,0)',
                            'fill': chart_type == 'area',
                            'tension': 0.1
                        })
                    
                    config['data'] = {
                        'labels': sorted_periods,
                        'datasets': datasets
                    }
                
                else:
                    # Sin agrupación, un solo dataset
                    periods = [item['period'] for item in chart_data]
                    values = [item['value'] for item in chart_data]
                    
                    config['data'] = {
                        'labels': periods,
                        'datasets': [{
                            'label': saved_chart.y_axis_field,
                            'data': values,
                            'borderColor': colors[0],
                            'backgroundColor': colors[0] if chart_type == 'area' else 'rgba(0,0,0,0)',
                            'fill': chart_type == 'area',
                            'tension': 0.1
                        }]
                    }
            
            elif chart_type == 'scatter':
                # Detectar si hay grupos
                has_groups = any('group' in item for item in chart_data)
                
                if has_groups:
                    # Agrupar datos por el campo de grupo
                    grouped_data = {}
                    
                    for item in chart_data:
                        group = item.get('group', 'Sin grupo')
                        
                        if group not in grouped_data:
                            grouped_data[group] = []
                        
                        grouped_data[group].append({
                            'x': item['x'],
                            'y': item['y']
                        })
                    
                    # Crear dataset para cada grupo
                    datasets = []
                    for i, (group, points) in enumerate(grouped_data.items()):
                        color_index = i % len(colors)
                        
                        datasets.append({
                            'label': str(group),
                            'data': points,
                            'backgroundColor': colors[color_index],
                            'pointRadius': 5,
                            'pointHoverRadius': 8
                        })
                    
                    config['data'] = {
                        'datasets': datasets
                    }
                
                else:
                    # Sin agrupación, un solo dataset
                    points = [{'x': item['x'], 'y': item['y']} for item in chart_data]
                    
                    config['data'] = {
                        'datasets': [{
                            'label': f"{saved_chart.x_axis_field} vs {saved_chart.y_axis_field}",
                            'data': points,
                            'backgroundColor': colors[0],
                            'pointRadius': 5,
                            'pointHoverRadius': 8
                        }]
                    }
            
            return config
            
        except Exception as e:
            logger.error(f"Error generando configuración Chart.js: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': str(e)}
    
    def generate_recharts_config(self, chart_type, chart_data, saved_chart):
        """Genera configuración para Recharts (React)"""
        try:
            # Obtener información del tipo de gráfico
            chart_info = self.CHART_TYPES.get(chart_type, self.CHART_TYPES['bar'])
            
            # Verificar que chart_info sea un diccionario
            if not isinstance(chart_info, dict):
                logger.error(f"Tipo de gráfico no válido: {chart_type}")
                return {'error': f'Tipo de gráfico no válido: {chart_type}'}
                
            recharts_component = chart_info.get('recharts_component', 'BarChart')
            
            # Obtener esquema de colores
            color_scheme = saved_chart.color_scheme or 'default'
            colors = self.COLOR_PALETTES.get(color_scheme, self.COLOR_PALETTES['default'])
            
            # Asegurar que chart_config sea un diccionario
            # AQUÍ ESTÁ LA CORRECCIÓN PRINCIPAL
            chart_config = self.ensure_dict(saved_chart.chart_config)
            
            # Configuración básica
            config = {
                'component': recharts_component,
                'title': saved_chart.title,
                'data': chart_data,
                'colors': colors,
                'width': chart_config.get('width', 600),  # Ahora es seguro usar .get()
                'height': chart_config.get('height', 400),
                'margin': {
                    'top': 20,
                    'right': 30,
                    'left': 20,
                    'bottom': 50
                }
            }
            
            # Aplicar opciones específicas del tipo de gráfico
            if 'recharts_options' in chart_info:
                # Asegurar que recharts_options sea un diccionario
                recharts_options = self.ensure_dict(chart_info.get('recharts_options'))
                for key, value in recharts_options.items():
                    config[key] = value
            
            # Añadir configuración específica según el tipo de gráfico
            if chart_type in ['bar', 'horizontal-bar']:
                config['xAxisDataKey'] = 'label'
                config['yAxisDataKey'] = 'value'
                config['barDataKey'] = 'value'
                
                if chart_type == 'horizontal-bar':
                    config['layout'] = 'horizontal'
                    config['xAxisDataKey'], config['yAxisDataKey'] = config['yAxisDataKey'], config['xAxisDataKey']
            
            elif chart_type in ['line', 'area']:
                # Verificar si los datos están agrupados
                has_groups = any('group' in item for item in chart_data)
                
                if has_groups:
                    # Transformar datos para Recharts
                    # Recharts necesita un formato diferente para datos agrupados
                    transformed_data = {}
                    all_groups = set()
                    
                    for item in chart_data:
                        period = item['period']
                        group = item.get('group', 'default')
                        value = item['value']
                        
                        if period not in transformed_data:
                            transformed_data[period] = {'period': period}
                        
                        transformed_data[period][group] = value
                        all_groups.add(group)
                    
                    config['data'] = list(transformed_data.values())
                    config['xAxisDataKey'] = 'period'
                    config['groups'] = list(all_groups)
                    config['lineDataKeys'] = list(all_groups)
                
                else:
                    # Datos no agrupados
                    config['xAxisDataKey'] = 'period'
                    config['yAxisDataKey'] = 'value'
                    config['lineDataKey'] = 'value'
            
            elif chart_type in ['pie', 'donut']:
                config['nameKey'] = 'label'
                config['dataKey'] = 'value'
                
                if chart_type == 'donut':
                    config['innerRadius'] = '60%'
                    config['outerRadius'] = '80%'
            
            elif chart_type == 'scatter':
                config['xAxisDataKey'] = 'x'
                config['yAxisDataKey'] = 'y'
                config['dataKey'] = 'y'
                
                # Verificar si los datos están agrupados
                has_groups = any('group' in item for item in chart_data)
                
                if has_groups:
                    # Transformar datos para agruparlos
                    grouped_data = {}
                    
                    for item in chart_data:
                        group = item.get('group', 'default')
                        
                        if group not in grouped_data:
                            grouped_data[group] = []
                        
                        grouped_data[group].append({
                            'x': item['x'],
                            'y': item['y']
                        })
                    
                    config['groupedData'] = grouped_data
                    config['groups'] = list(grouped_data.keys())
            
            return config
            
        except Exception as e:
            logger.error(f"Error generando configuración Recharts: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': str(e)}