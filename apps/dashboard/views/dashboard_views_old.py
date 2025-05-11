from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from apps.dashboard.models.dashboard_models import ChartType, SavedChart, Dashboard, DashboardWidget, DataReport
from apps.dashboard.services.model_inspector import ModelInspector
from apps.dashboard.services.data_processor import DataProcessor
from apps.dashboard.services.chart_generator import ChartGenerator
import traceback
from django.apps import apps
import json
import logging

logger = logging.getLogger(__name__)

class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Vista principal del dashboard"""
    template_name = 'dashboard/dashboard_home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener dashboard activo o predeterminado
        dashboard_id = self.request.GET.get('dashboard_id')
        
        if dashboard_id:
            dashboard = Dashboard.objects.filter(
                id=dashboard_id, 
                created_by=self.request.user
            ).first()
        else:
            # Obtener dashboard predeterminado o crear uno
            dashboard = Dashboard.objects.filter(
                created_by=self.request.user,
                is_default=True
            ).first()
            
            if not dashboard:
                # Si no existe un dashboard predeterminado, buscar cualquiera
                dashboard = Dashboard.objects.filter(
                    created_by=self.request.user
                ).first()
                
                if not dashboard:
                    # Si no hay dashboards, crear uno predeterminado
                    dashboard = Dashboard.objects.create(
                        name=_('Mi Dashboard'),
                        created_by=self.request.user,
                        is_default=True
                    )
        
        # Obtener todos los dashboards del usuario
        dashboards = Dashboard.objects.filter(created_by=self.request.user).order_by('name')
        
        # Obtener widgets del dashboard
        widgets = DashboardWidget.objects.filter(dashboard=dashboard).select_related('saved_chart')
        
        # Generar configuraciones de los gráficos
        chart_generator = ChartGenerator()
        widget_configs = []
        
        for widget in widgets:
            try:
                chart_config = chart_generator.generate_chart_config(widget.saved_chart, format='chartjs')
                
                widget_configs.append({
                    'id': widget.id,
                    'chart_id': widget.saved_chart.id,
                    'title': widget.saved_chart.title,
                    'description': widget.saved_chart.description,
                    'position_x': widget.position_x,
                    'position_y': widget.position_y,
                    'width': widget.width,
                    'height': widget.height,
                    'chart_config': chart_config,
                    'widget_config': widget.widget_config
                })
            except Exception as e:
                logger.error(f"Error generando configuración para widget {widget.id}: {str(e)}")
        
        context.update({
            'dashboard': dashboard,
            'dashboards': dashboards,
            'widget_configs': json.dumps(widget_configs),
            'charts_count': SavedChart.objects.filter(created_by=self.request.user).count(),
            'reports_count': DataReport.objects.filter(created_by=self.request.user).count()
        })
        
        return context

class ChartBuilderView(LoginRequiredMixin, TemplateView):
    """Vista para construir gráficos"""
    template_name = 'dashboard/chart_builder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener tipos de gráficos
        chart_types = ChartType.objects.all().order_by('name')
        
        # Obtener el explorador de modelos
        model_inspector = ModelInspector()
        models = model_inspector.get_all_models()
        
        # Procesar modelos para el frontend
        models_json = json.dumps([{
            'app_label': model['app_label'],
            'model_name': model['model_name'],
            'verbose_name': str(model['verbose_name']),
            'content_type_id': model['content_type_id'],
            'is_audit_model': model['is_audit_model'],
            'object_count': model['object_count']
        } for model in models])
        
        context.update({
            'chart_types': chart_types,
            'models': models,
            'models_json': models_json,
            'chart_id': self.kwargs.get('pk', None)
        })
        
        return context

class SavedChartListView(LoginRequiredMixin, ListView):
    """Vista de lista de gráficos guardados"""
    model = SavedChart
    template_name = 'dashboard/saved_charts.html'
    context_object_name = 'charts'
    paginate_by = 9  # o el número que prefieras
    
    def get_queryset(self):
        queryset = SavedChart.objects.all()
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['dashboards'] = Dashboard.objects.filter(created_by=self.request.user).order_by('name')
        return context

class SavedChartDetailView(LoginRequiredMixin, DetailView):
    """
    Vista para mostrar y editar un gráfico guardado.
    Proporciona la configuración necesaria para el formulario de edición
    y la visualización previa del gráfico.
    """
    model = SavedChart
    template_name = 'dashboard/chart_form.html'
    context_object_name = 'chart'

    def get_context_data(self, **kwargs):
        """
        Prepara el contexto para la plantilla, incluyendo la configuración
        del gráfico y los datos necesarios para el formulario.
        """
        context = super().get_context_data(**kwargs)
        chart = self.object
        cache_key = f'chart_{chart.id}_config'

        try:
            # PARCHE ESPECÍFICO PARA EL GRÁFICO 9
            if chart.id == 9:
                print("*** APLICANDO PARCHE ESPECÍFICO PARA GRÁFICO 9 ***")
                # Limpiar la caché para este gráfico
                cache.delete(cache_key)
                
                # Proporcionar una configuración manual para este gráfico
                # Esto es una configuración mínima para Chart.js que funciona
                chart_config = {
                    'type': 'bar',  # Asumimos que es un gráfico de barras
                    'data': {
                        'labels': ["No hay datos disponibles"],
                        'datasets': [{
                            'label': chart.title,
                            'data': [0],
                            'backgroundColor': '#4e79a7'
                        }]
                    },
                    'options': {
                        'responsive': True,
                        'maintainAspectRatio': False,
                        'plugins': {
                            'title': {
                                'display': True,
                                'text': chart.title,
                                'font': {'size': 16}
                            },
                            'subtitle': {
                                'display': True,
                                'text': 'Este gráfico necesita ser reconfigurado',
                                'font': {'style': 'italic'}
                            }
                        }
                    }
                }
                
                # Preparar datos para el template
                models_json = json.dumps(self.get_models())
                chart_types_json = json.dumps(self.get_chart_types())
                dashboards = self.get_dashboards()
                
                # Actualizar contexto con datos para el formulario
                context.update({
                    'chart_config': chart_config,
                    'dashboards': dashboards,
                    'models_json': models_json,
                    'chart_types_json': chart_types_json,
                    'warning_message': 'Este gráfico necesita reconfiguración. Por favor edite y guarde la configuración.'
                })
                
                # NUEVO: Impresión detallada de datos para depuración
                self._print_debug_info(chart, chart_config, models_json, chart_types_json, dashboards, context)
                print("*** PARCHE APLICADO CON ÉXITO ***")
                return context
            
            # INICIO DEL CÓDIGO NORMAL PARA OTROS GRÁFICOS
            # Convertir campos JSON a diccionarios si son strings
            if isinstance(chart.chart_config, str):
                try:
                    chart.chart_config = json.loads(chart.chart_config)
                    print(f"Convertido chart_config de string a dict para gráfico {chart.id}")
                except:
                    chart.chart_config = {}
                    print(f"Error al convertir chart_config, se usará dict vacío para gráfico {chart.id}")
            
            if isinstance(chart.filter_config, str):
                try:
                    chart.filter_config = json.loads(chart.filter_config)
                    print(f"Convertido filter_config de string a dict para gráfico {chart.id}")
                except:
                    chart.filter_config = {}
                    print(f"Error al convertir filter_config, se usará dict vacío para gráfico {chart.id}")

            # Intentar obtener del cache
            chart_config = cache.get(cache_key)
            
            # Validar que chart_config sea un diccionario y no un string
            if isinstance(chart_config, str):
                try:
                    chart_config = json.loads(chart_config)
                except json.JSONDecodeError:
                    logger.warning(f"Error decodificando JSON en caché para gráfico {chart.id}")
                    chart_config = None
            
            # Si no hay datos en cache o son inválidos, regenerar
            if not chart_config:
                logger.info(f"Generando configuración para gráfico {chart.id}")
                chart_config = ChartGenerator().generate_chart_config(chart)
                
                # Verificar si chart_config contiene solo un error
                if isinstance(chart_config, dict) and len(chart_config) == 1 and 'error' in chart_config:
                    error_message = chart_config['error']
                    raise Exception(f"Error en generación de gráfico: {error_message}")
                
                # Validar tipo de datos correcto
                if not isinstance(chart_config, (dict, list)):
                    raise TypeError(f"La configuración del gráfico debe ser un diccionario o lista, no {type(chart_config)}")
                
                # Guardar en caché
                cache.set(cache_key, chart_config, 900)  # 15 minutos
            
            # Preparar datos para el template
            models_json = json.dumps(self.get_models())
            chart_types_json = json.dumps(self.get_chart_types())
            dashboards = self.get_dashboards()
            
            # Actualizar contexto con todos los datos necesarios
            context.update({
                'chart_config': chart_config,
                'dashboards': dashboards,
                'models_json': models_json,
                'chart_types_json': chart_types_json,
                'error_message': None  # Explícitamente indicar que no hay error
            })
            
            # NUEVO: Impresión detallada de datos para depuración
            self._print_debug_info(chart, chart_config, models_json, chart_types_json, dashboards, context)
            
        except Exception as e:
            # Manejar el error de manera elegante
            logger.error(f"Error obteniendo datos para gráfico {chart.id}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # DEBUG: Imprimir el error en detalle
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            
            # Proporcionar un contexto mínimo para mostrar un mensaje de error
            context.update({
                'error_message': f"Error al cargar el gráfico: {str(e)}",
                'chart_config': None,  # No enviar configuración con error
                'dashboards': self.get_dashboards(),
                'models_json': json.dumps(self.get_models()),
                'chart_types_json': json.dumps(self.get_chart_types())
            })
            
            # Imprimir contexto de error
            print("\n======= CONTEXTO DE ERROR ENVIADO AL TEMPLATE =======")
            print(f"error_message: {context.get('error_message')}")
            print(f"chart_config: {context.get('chart_config')}")
            print(f"dashboards count: {len(context.get('dashboards', []))}")
            print(f"models_json length: {len(context.get('models_json', ''))}")
            print(f"chart_types_json length: {len(context.get('chart_types_json', ''))}")
            print("====================================================\n")
            
        return context
    
    def _print_debug_info(self, chart, chart_config, models_json, chart_types_json, dashboards, context):
        """Método auxiliar para imprimir información de depuración"""
        print("\n" + "="*50)
        print(f"DATOS COMPLETOS PARA EL GRÁFICO {chart.id}: {chart.title}")
        print("="*50)
        
        print("\n--- INFORMACIÓN DEL GRÁFICO ---")
        print(f"ID: {chart.id}")
        print(f"Título: {chart.title}")
        print(f"Tipo: {chart.chart_type}")
        print(f"Campos: X={chart.x_axis_field}, Y={chart.y_axis_field}")
        print(f"Es público: {chart.is_public}")
        print(f"Es favorito: {chart.is_favorite}")
        
        print("\n--- CONFIGURACIÓN DEL GRÁFICO ---")
        print(f"Tipo de datos: {type(chart_config)}")
        if isinstance(chart_config, dict):
            print("Claves principales:")
            for key in chart_config.keys():
                print(f"  - {key}")
            
            if 'type' in chart_config:
                print(f"Tipo de gráfico: {chart_config['type']}")
            
            if 'data' in chart_config and isinstance(chart_config['data'], dict):
                data_keys = chart_config['data'].keys()
                print(f"Claves de datos: {', '.join(data_keys)}")
                
                if 'datasets' in chart_config['data'] and isinstance(chart_config['data']['datasets'], list):
                    print(f"Número de datasets: {len(chart_config['data']['datasets'])}")
                
                if 'labels' in chart_config['data'] and isinstance(chart_config['data']['labels'], list):
                    print(f"Número de etiquetas: {len(chart_config['data']['labels'])}")
                    if len(chart_config['data']['labels']) > 0:
                        print(f"Primera etiqueta: {chart_config['data']['labels'][0]}")
        else:
            print(f"Valor: {chart_config}")
        
        print("\n--- DATOS PARA EL FORMULARIO ---")
        print(f"Dashboards disponibles: {dashboards.count()}")
        print(f"Modelos disponibles: {len(json.loads(models_json))}")
        print(f"Tipos de gráficos disponibles: {len(json.loads(chart_types_json))}")
        
        print("\n--- KEYS DEL CONTEXTO ---")
        for key in context.keys():
            if key not in ['view', 'chart_config', 'dashboards', 'models_json', 'chart_types_json']:
                print(f"  - {key}: {type(context[key])}")
        
        print("="*50 + "\n")

    def get_models(self):
        """
        Obtiene la lista de modelos disponibles para crear gráficos.
        Retorna una lista de nombres de modelos.
        """
        from django.apps import apps  # Importación local para asegurar acceso
        return [model._meta.model_name for model in apps.get_models()]

    def get_chart_types(self):
        """
        Obtiene los tipos de gráficos disponibles para seleccionar.
        Retorna una lista de claves de tipos de gráficos.
        """
        return list(ChartGenerator.CHART_TYPES.keys())

    def get_dashboards(self):
        """
        Obtiene los dashboards del usuario actual para permitir
        asignar el gráfico a un dashboard.
        """
        return Dashboard.objects.filter(
            created_by=self.request.user
        ).order_by('name')  

class SaveChartView(LoginRequiredMixin, FormView):
    """Vista para guardar un gráfico"""
    template_name = 'dashboard/chart_builder.html'
    
    def post(self, request, *args, **kwargs):
        try:
            # Obtener datos del formulario
            data = json.loads(request.body)
            
            # Obtener o crear el gráfico
            chart_id = data.get('chart_id')
            
            if chart_id:
                # Actualizar gráfico existente
                chart = get_object_or_404(SavedChart, id=chart_id, created_by=request.user)
                
                chart.title = data.get('title', chart.title)
                chart.description = data.get('description', chart.description)
                chart.chart_type_id = data.get('chart_type_id', chart.chart_type_id)
                chart.model_content_type_id = data.get('model_content_type_id', chart.model_content_type_id)
                chart.x_axis_field = data.get('x_axis_field', chart.x_axis_field)
                chart.y_axis_field = data.get('y_axis_field', chart.y_axis_field)
                chart.filter_config = data.get('filter_config', chart.filter_config)
                chart.chart_config = data.get('chart_config', chart.chart_config)
                chart.color_scheme = data.get('color_scheme', chart.color_scheme)
                chart.is_public = data.get('is_public', chart.is_public)
                
                chart.save()
                
                return JsonResponse({
                    'success': True,
                    'message': _('Gráfico actualizado correctamente'),
                    'chart_id': chart.id
                })
                
            else:
                # Crear nuevo gráfico
                chart = SavedChart(
                    title=data.get('title', _('Nuevo gráfico')),
                    description=data.get('description', ''),
                    chart_type_id=data.get('chart_type_id'),
                    model_content_type_id=data.get('model_content_type_id'),
                    x_axis_field=data.get('x_axis_field'),
                    y_axis_field=data.get('y_axis_field'),
                    filter_config=data.get('filter_config'),
                    chart_config=data.get('chart_config'),
                    color_scheme=data.get('color_scheme', 'default'),
                    created_by=request.user,
                    is_public=data.get('is_public', False)
                )
                
                chart.save()
                
                return JsonResponse({
                    'success': True,
                    'message': _('Gráfico guardado correctamente'),
                    'chart_id': chart.id
                })
                
        except Exception as e:
            logger.error(f"Error guardando gráfico: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

class GetModelFieldsView(LoginRequiredMixin, TemplateView):
    """API para obtener campos de un modelo"""
    
    def get(self, request, *args, **kwargs):
        try:
            app_label = request.GET.get('app_label')
            model_name = request.GET.get('model_name')
            
            if not app_label or not model_name:
                return JsonResponse({
                    'success': False,
                    'message': _('Debe especificar app_label y model_name')
                }, status=400)
            
            # Obtener campos del modelo
            model_inspector = ModelInspector()
            fields = model_inspector.get_model_fields(app_label, model_name)
            
            return JsonResponse({
                'success': True,
                'fields': fields
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo campos: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

class GetFieldDistributionView(LoginRequiredMixin, TemplateView):
    """API para obtener la distribución de valores de un campo"""
    
    def get(self, request, *args, **kwargs):
        try:
            app_label = request.GET.get('app_label')
            model_name = request.GET.get('model_name')
            field_name = request.GET.get('field_name')
            
            if not app_label or not model_name or not field_name:
                return JsonResponse({
                    'success': False,
                    'message': _('Debe especificar app_label, model_name y field_name')
                }, status=400)
            
            # Obtener distribución del campo
            model_inspector = ModelInspector()
            distribution = model_inspector.get_field_value_distribution(app_label, model_name, field_name)
            
            return JsonResponse({
                'success': True,
                'distribution': distribution
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo distribución: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

class GetChartPreviewView(LoginRequiredMixin, TemplateView):
    """API para obtener una vista previa del gráfico"""
    
    def post(self, request, *args, **kwargs):
        try:
            # Obtener datos del formulario
            data = json.loads(request.body)
            
            # Crear gráfico temporal
            temp_chart = SavedChart(
                title=data.get('title', _('Vista previa')),
                chart_type_id=data.get('chart_type_id'),
                model_content_type_id=data.get('model_content_type_id'),
                x_axis_field=data.get('x_axis_field'),
                y_axis_field=data.get('y_axis_field'),
                filter_config=data.get('filter_config'),
                chart_config=data.get('chart_config'),
                color_scheme=data.get('color_scheme', 'default'),
                created_by=request.user
            )
            
            # Generar configuración del gráfico
            chart_generator = ChartGenerator()
            chart_config = chart_generator.generate_chart_config(temp_chart, format='chartjs')
            
            return JsonResponse({
                'success': True,
                'chart_config': chart_config
            })
            
        except Exception as e:
            logger.error(f"Error generando vista previa: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

class AddChartToDashboardView(LoginRequiredMixin, TemplateView):
    """API para agregar un gráfico a un dashboard"""
    
    def post(self, request, *args, **kwargs):
        try:
            # Obtener datos del formulario
            chart_id = request.POST.get('chart_id')
            dashboard_id = request.POST.get('dashboard_id')
            
            if not chart_id or not dashboard_id:
                return JsonResponse({
                    'success': False,
                    'message': _('Debe especificar chart_id y dashboard_id')
                }, status=400)
            
            # Obtener objetos
            chart = get_object_or_404(SavedChart, id=chart_id, created_by=request.user)
            dashboard = get_object_or_404(Dashboard, id=dashboard_id, created_by=request.user)
            
            # Verificar si ya existe un widget con este gráfico en el dashboard
            existing_widget = DashboardWidget.objects.filter(
                dashboard=dashboard,
                saved_chart=chart
            ).first()
            
            if existing_widget:
                return JsonResponse({
                    'success': False,
                    'message': _('Este gráfico ya está en el dashboard')
                }, status=400)
            
            # Calcular posición para el nuevo widget
            # Por defecto, lo colocamos en la primera fila disponible
            max_y = DashboardWidget.objects.filter(dashboard=dashboard).order_by('-position_y').values_list('position_y', flat=True).first() or -1
            
            # Crear widget
            widget = DashboardWidget.objects.create(
                dashboard=dashboard,
                saved_chart=chart,
                position_y=max_y + 1,
                position_x=0,
                width=4,
                height=3
            )
            
            return JsonResponse({
                'success': True,
                'message': _('Gráfico agregado al dashboard'),
                'widget_id': widget.id
            })
            
        except Exception as e:
            logger.error(f"Error agregando gráfico al dashboard: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

class DataReportListView(LoginRequiredMixin, ListView):
    """Vista de lista de informes de datos"""
    model = DataReport
    template_name = 'dashboard/data_reports.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        queryset = DataReport.objects.filter(
            created_by=self.request.user
        ).order_by('-created_at')
        
        # Filtrar por búsqueda
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ChartDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar un gráfico guardado"""
    model = SavedChart
    template_name = 'dashboard/chart_confirm_delete.html'
    context_object_name = 'chart'
    success_url = reverse_lazy('dashboard:chart_list')
    
    def get_queryset(self):
        # Filtrar para asegurar que solo el propietario pueda eliminar sus gráficos
        return SavedChart.objects.filter(created_by=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        # Obtener el objeto
        self.object = self.get_object()
        
        # Verificar si hay widgets usando este gráfico
        widgets = DashboardWidget.objects.filter(saved_chart=self.object)
        
        # Eliminar widgets relacionados primero
        if widgets.exists():
            widget_count = widgets.count()
            dashboard_ids = set(widgets.values_list('dashboard_id', flat=True))
            widgets.delete()
            
            # Notificar al usuario
            messages.warning(
                request, 
                _('Se eliminaron %(count)d widgets relacionados con este gráfico de %(dash_count)d dashboards.') % {
                    'count': widget_count,
                    'dash_count': len(dashboard_ids)
                }
            )
        
        # Eliminar el gráfico
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, _('Gráfico eliminado correctamente.'))
        
        # Si es una solicitud AJAX, devolver respuesta JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect_url': success_url})
        
        return HttpResponseRedirect(success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Contar widgets relacionados
        widget_count = DashboardWidget.objects.filter(saved_chart=self.object).count()
        context['widget_count'] = widget_count
        
        # Agregar dashboards al contexto para el sidebar
        context['dashboards'] = Dashboard.objects.filter(created_by=self.request.user).order_by('name')
        
        return context

class ToggleChartFavoriteView(LoginRequiredMixin, UpdateView):
    """Vista para marcar/desmarcar un gráfico como favorito"""
    model = SavedChart
    fields = ['is_favorite']
    http_method_names = ['post']
    
    def get_object(self, queryset=None):
        # Obtener datos del cuerpo JSON
        try:
            data = json.loads(self.request.body)
            chart_id = data.get('chart_id')
            self.is_favorite = data.get('is_favorite', False)
            
            if not chart_id:
                raise ValueError(_('ID de gráfico no proporcionado'))
                
            # Obtener el gráfico asegurando que pertenece al usuario actual
            return self.model.objects.get(id=chart_id, created_by=self.request.user)
            
        except json.JSONDecodeError:
            logger.error("Error decodificando JSON en solicitud")
            raise ValueError(_('Formato de solicitud inválido'))
        except self.model.DoesNotExist:
            logger.error(f"Gráfico no encontrado o no pertenece al usuario")
            raise ValueError(_('Gráfico no encontrado'))
    
    def form_valid(self, form):
        # Aquí normalmente se procesaría el formulario,
        # pero como estamos usando JSON, lo manejamos manualmente
        chart = self.object
        chart.is_favorite = self.is_favorite
        chart.save(update_fields=['is_favorite', 'updated_at'])
        
        # Determinar mensaje según la acción
        if self.is_favorite:
            message = _('Gráfico marcado como favorito')
        else:
            message = _('Gráfico eliminado de favoritos')
        
        return JsonResponse({
            'success': True,
            'message': message,
            'is_favorite': chart.is_favorite,
            'chart_id': chart.id
        })
    
    def form_invalid(self, form):
        return JsonResponse({
            'success': False,
            'message': _('Error en el formulario'),
            'errors': form.errors
        }, status=400)
    
    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            form = self.get_form()
            return self.form_valid(form)
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Error al cambiar estado de favorito: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': _('Error inesperado al procesar la solicitud')
            }, status=500)

def create_user_dashboard(user, title, description, layout_config=None):
    """
    Crea un dashboard personalizado para un usuario específico
    """
    dashboard = Dashboard.objects.create(
        name=title,
        description=description,
        is_default=False,
        layout_config=layout_config or {},
        created_by=user
    )
    
    # Aquí puedes añadir widgets predeterminados o dejar el dashboard vacío
    # para que el usuario lo personalice
    
    return dashboard

@login_required
def create_personal_dashboard(request):
    if request.method == 'POST':
        # Obtener datos del formulario
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        # Crear dashboard personalizado
        dashboard = create_user_dashboard(
            user=request.user,
            title=title,
            description=description
        )
        
        messages.success(request, f'Dashboard "{title}" creado exitosamente.')
        return redirect('dashboard:edit', pk=dashboard.id)
    
    return render(request, 'dashboard/create_dashboard.html')

