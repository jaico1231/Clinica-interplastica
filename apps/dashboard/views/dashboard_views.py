from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.dashboard.forms.dashboardform import (
    SavedChartForm,
    DashboardForm,
    DashboardWidgetForm,
    DataReportForm
    )
from apps.dashboard.models.dashboard_models import ChartType, SavedChart, Dashboard, DashboardWidget, DataReport
from apps.dashboard.serializers.dashboard_serializers import (
    ChartTypeSerializer,
    SavedChartSerializer, 
    DashboardSerializer, 
    DashboardWidgetSerializer,
    DataReportSerializer
    )
# from .serializers import (
#     ChartTypeSerializer, 
#     SavedChartSerializer, 
#     DashboardSerializer, 
#     DashboardWidgetSerializer,
#     DataReportSerializer
# )
# from .forms import (
#     SavedChartForm, 
#     DashboardForm, 
#     DashboardWidgetForm,
#     DataReportForm
# )

import json

# Chart type views
class ChartTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint para tipos de gráficos - solo lectura ya que estos serán predefinidos"""
    queryset = ChartType.objects.all()
    serializer_class = ChartTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

# Saved Chart views
class SavedChartViewSet(viewsets.ModelViewSet):
    """API endpoint para gráficos guardados"""
    serializer_class = SavedChartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna gráficos creados por el usuario o gráficos públicos"""
        user = self.request.user
        return SavedChart.objects.filter(
            Q(created_by=user) | Q(is_public=True)
        ).active()
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.created_by != self.request.user:
            raise PermissionDenied(_("No tienes permiso para editar este gráfico"))
        serializer.save(modified_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """Retorna solo los gráficos favoritos del usuario"""
        queryset = self.get_queryset().filter(
            created_by=request.user,
            is_favorite=True
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Activa/desactiva el estado de favorito de un gráfico"""
        chart = self.get_object()
        if chart.created_by != request.user:
            return Response(
                {"detail": _("Solo puedes marcar como favorito tus propios gráficos")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        chart.is_favorite = not chart.is_favorite
        chart.save()
        return Response({"is_favorite": chart.is_favorite})
    
    @action(detail=True, methods=['get'])
    def generate_data(self, request, pk=None):
        """Genera los datos reales del gráfico basado en su configuración"""
        chart = self.get_object()
        
        # Obtener la clase del modelo
        model_class = chart.model_content_type.model_class()
        if not model_class:
            return Response(
                {"detail": _("Configuración de modelo inválida")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Comenzar con todos los objetos del modelo
        queryset = model_class.objects.all()
        
        # Aplicar filtros si están definidos
        if chart.filter_config:
            try:
                # Lógica de filtro basada en filter_config
                for field, value in chart.filter_config.items():
                    filter_dict = {field: value}
                    queryset = queryset.filter(**filter_dict)
            except Exception as e:
                return Response(
                    {"detail": _("Error al aplicar filtros: {}").format(str(e))},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Obtener datos de los ejes x e y
        try:
            # Para gráficos simples, solo necesitamos recopilar valores x e y
            data = []
            
            # Caso especial para agregación de conteo
            if chart.y_axis_field == "count":
                # Agrupar por x_axis_field y contar
                result = {}
                for item in queryset:
                    x_value = getattr(item, chart.x_axis_field)
                    if x_value in result:
                        result[x_value] += 1
                    else:
                        result[x_value] = 1
                
                # Convertir al formato esperado por la biblioteca de gráficos
                for x_value, count in result.items():
                    data.append({
                        "x": x_value,
                        "y": count,
                        "label": str(x_value)
                    })
            else:
                # Recopilación de datos para otros gráficos
                for item in queryset:
                    x_value = getattr(item, chart.x_axis_field)
                    y_value = getattr(item, chart.y_axis_field)
                    data.append({
                        "x": x_value,
                        "y": y_value,
                        "label": str(x_value)
                    })
            
            return Response({
                "chart_type": chart.chart_type.code,
                "title": chart.title,
                "data": data,
                "config": chart.chart_config
            })
        
        except Exception as e:
            return Response(
                {"detail": _("Error al generar datos del gráfico: {}").format(str(e))},
                status=status.HTTP_400_BAD_REQUEST
            )

# Dashboard views
class DashboardViewSet(viewsets.ModelViewSet):
    """API endpoint para dashboards"""
    serializer_class = DashboardSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna dashboards creados por el usuario"""
        return Dashboard.objects.filter(created_by=self.request.user).active()
    
    def perform_create(self, serializer):
        # Verificar si está configurado como predeterminado, y desactivar cualquier valor predeterminado existente
        if serializer.validated_data.get('is_default', False):
            Dashboard.objects.filter(
                created_by=self.request.user, 
                is_default=True
            ).update(is_default=False)
        
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        instance = self.get_object()
        
        # Verificar si se está configurando como predeterminado y desactivar otros
        if serializer.validated_data.get('is_default', False) and not instance.is_default:
            Dashboard.objects.filter(
                created_by=self.request.user, 
                is_default=True
            ).update(is_default=False)
        
        serializer.save(modified_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Retorna el dashboard predeterminado para el usuario"""
        try:
            dashboard = Dashboard.objects.get(
                created_by=request.user,
                is_default=True
            )
            serializer = self.get_serializer(dashboard)
            return Response(serializer.data)
        except Dashboard.DoesNotExist:
            # Sin dashboard predeterminado, retornar el más reciente
            try:
                dashboard = Dashboard.objects.filter(
                    created_by=request.user
                ).active().latest('created_at')
                serializer = self.get_serializer(dashboard)
                return Response(serializer.data)
            except Dashboard.DoesNotExist:
                return Response(
                    {"detail": _("No se encontraron dashboards")},
                    status=status.HTTP_404_NOT_FOUND
                )
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Establece este dashboard como el predeterminado para el usuario"""
        dashboard = self.get_object()
        
        # Desactivar cualquier valor predeterminado existente
        Dashboard.objects.filter(
            created_by=request.user, 
            is_default=True
        ).update(is_default=False)
        
        # Establecer este como predeterminado
        dashboard.is_default = True
        dashboard.save()
        
        return Response({"detail": _("Dashboard predeterminado configurado exitosamente")})

# Dashboard Widget views
class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """API endpoint para widgets de dashboard"""
    serializer_class = DashboardWidgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna widgets para un dashboard específico"""
        dashboard_id = self.request.query_params.get('dashboard_id')
        if dashboard_id:
            return DashboardWidget.objects.filter(
                dashboard_id=dashboard_id,
                dashboard__created_by=self.request.user
            ).active()
        return DashboardWidget.objects.filter(
            dashboard__created_by=self.request.user
        ).active()
    
    def perform_create(self, serializer):
        dashboard = serializer.validated_data.get('dashboard')
        
        # Asegurar que el usuario sea propietario del dashboard
        if dashboard.created_by != self.request.user:
            raise PermissionDenied(_("No tienes permiso para añadir widgets a este dashboard"))
        
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        instance = self.get_object()
        dashboard = serializer.validated_data.get('dashboard', instance.dashboard)
        
        # Asegurar que el usuario sea propietario del dashboard
        if dashboard.created_by != self.request.user:
            raise PermissionDenied(_("No tienes permiso para modificar este dashboard"))
        
        serializer.save(modified_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def update_layout(self, request):
        """Actualiza las posiciones de múltiples widgets a la vez"""
        widgets_data = request.data
        if not isinstance(widgets_data, list):
            return Response(
                {"detail": _("Se esperaba una lista de widgets")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_widgets = []
        for widget_data in widgets_data:
            try:
                widget_id = widget_data.get('id')
                if not widget_id:
                    continue
                
                widget = DashboardWidget.objects.get(
                    id=widget_id,
                    dashboard__created_by=request.user
                )
                
                # Actualizar posición y tamaño
                if 'position_x' in widget_data:
                    widget.position_x = widget_data['position_x']
                if 'position_y' in widget_data:
                    widget.position_y = widget_data['position_y']
                if 'width' in widget_data:
                    widget.width = widget_data['width']
                if 'height' in widget_data:
                    widget.height = widget_data['height']
                
                widget.modified_by = request.user
                widget.save()
                updated_widgets.append(widget.id)
            
            except DashboardWidget.DoesNotExist:
                continue
        
        return Response({
            "detail": _("Actualizados {} widgets").format(len(updated_widgets)),
            "updated": updated_widgets
        })

# DataReport views
class DataReportViewSet(viewsets.ModelViewSet):
    """API endpoint para informes de datos"""
    serializer_class = DataReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna informes creados por el usuario"""
        return DataReport.objects.filter(created_by=self.request.user).active()
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.created_by != self.request.user:
            raise PermissionDenied(_("No tienes permiso para editar este informe"))
        serializer.save(modified_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Genera los datos del informe"""
        report = self.get_object()
        
        # Actualizar marca de tiempo de última generación
        report.last_generated = timezone.now()
        report.save(update_fields=['last_generated', 'modified_at', 'modified_by'])
        
        # Aquí implementaríamos la lógica real de generación de informes
        # Esto dependería de los requisitos específicos
        
        return Response({
            "detail": _("Generación de informe iniciada"),
            "report_id": report.id,
            "last_generated": report.last_generated
        })

# Vistas basadas en funciones para operaciones más complejas

@login_required
def model_fields(request):
    """Retorna los campos disponibles para un modelo dado"""
    content_type_id = request.GET.get('content_type_id')
    if not content_type_id:
        return JsonResponse({"error": _("Se requiere el ID del tipo de contenido")}, status=400)
    
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        model_class = content_type.model_class()
        
        if not model_class:
            return JsonResponse({"error": _("Tipo de contenido inválido")}, status=400)
        
        # Obtener todos los campos del modelo
        fields = []
        for field in model_class._meta.get_fields():
            # Omitir relaciones muchos a muchos y relaciones inversas
            if field.is_relation and (field.many_to_many or field.one_to_many):
                continue
            
            # Agregar información del campo
            field_info = {
                "name": field.name,
                "verbose_name": str(field.verbose_name),
                "type": field.__class__.__name__
            }
            fields.append(field_info)
        
        return JsonResponse({"fields": fields})
    
    except ContentType.DoesNotExist:
        return JsonResponse({"error": _("Tipo de contenido no encontrado")}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def available_models(request):
    """Retorna una lista de modelos que pueden usarse para gráficos"""
    # Puedes filtrar esta lista para incluir solo ciertos modelos
    content_types = ContentType.objects.all().order_by('app_label', 'model')
    
    models = []
    for ct in content_types:
        # Opcionalmente omitir ciertos modelos que no deberían usarse para gráficos
        if ct.model in ['session', 'contenttype', 'permission']:
            continue
        
        models.append({
            "id": ct.id,
            "app_label": ct.app_label,
            "model": ct.model,
            "name": f"{ct.app_label}.{ct.model}"
        })
    
    return JsonResponse({"models": models})

@login_required
def chart_preview(request):
    """Genera una vista previa de un gráfico sin guardarlo"""
    if request.method != 'POST':
        return JsonResponse({"error": _("Se requiere método POST")}, status=405)
    
    try:
        data = json.loads(request.body)
        
        content_type_id = data.get('model_content_type')
        x_axis_field = data.get('x_axis_field')
        y_axis_field = data.get('y_axis_field')
        filter_config = data.get('filter_config', {})
        
        if not all([content_type_id, x_axis_field, y_axis_field]):
            return JsonResponse({"error": _("Faltan campos requeridos")}, status=400)
        
        # Obtener la clase del modelo
        try:
            content_type = ContentType.objects.get(id=content_type_id)
            model_class = content_type.model_class()
            
            if not model_class:
                return JsonResponse({"error": _("Modelo inválido")}, status=400)
        except ContentType.DoesNotExist:
            return JsonResponse({"error": _("Tipo de contenido no encontrado")}, status=404)
        
        # Comenzar con todos los objetos
        queryset = model_class.objects.all()
        
        # Aplicar filtros si están definidos
        if filter_config:
            try:
                # Lógica de filtro basada en filter_config
                for field, value in filter_config.items():
                    filter_dict = {field: value}
                    queryset = queryset.filter(**filter_dict)
            except Exception as e:
                return JsonResponse({"error": _("Error al aplicar filtros: {}").format(str(e))}, status=400)
        
        # Generar datos del gráfico
        chart_data = []
        
        # Caso especial para agregación de conteo
        if y_axis_field == "count":
            # Agrupar por x_axis_field y contar
            result = {}
            for item in queryset:
                x_value = getattr(item, x_axis_field)
                if x_value in result:
                    result[x_value] += 1
                else:
                    result[x_value] = 1
            
            # Convertir al formato esperado por la biblioteca de gráficos
            for x_value, count in result.items():
                chart_data.append({
                    "x": x_value,
                    "y": count,
                    "label": str(x_value)
                })
        else:
            # Recopilación de datos regular
            for item in queryset:
                x_value = getattr(item, x_axis_field)
                y_value = getattr(item, y_axis_field)
                chart_data.append({
                    "x": x_value,
                    "y": y_value,
                    "label": str(x_value)
                })
        
        return JsonResponse({
            "chart_type": data.get('chart_type'),
            "title": data.get('title', _('Vista previa del gráfico')),
            "data": chart_data
        })
    
    except json.JSONDecodeError:
        return JsonResponse({"error": _("JSON inválido")}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Vistas basadas en plantillas

class ChartTypeListView(LoginRequiredMixin, ListView):
    """Vista para listar todos los tipos de gráficos"""
    model = ChartType
    template_name = 'charts/chart_type_list.html'
    context_object_name = 'chart_types'

class SavedChartListView(LoginRequiredMixin, ListView):
    """Vista para listar los gráficos guardados del usuario"""
    template_name = 'charts/saved_chart_list.html'
    context_object_name = 'charts'
    
    def get_queryset(self):
        return SavedChart.objects.filter(
            Q(created_by=self.request.user) | Q(is_public=True)
        ).active()

class SavedChartCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear un nuevo gráfico"""
    model = SavedChart
    form_class = SavedChartForm
    template_name = 'charts/saved_chart_form.html'
    success_url = reverse_lazy('saved_chart_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class SavedChartUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar un gráfico existente"""
    model = SavedChart
    form_class = SavedChartForm
    template_name = 'charts/saved_chart_form.html'
    success_url = reverse_lazy('saved_chart_list')
    
    def get_queryset(self):
        return SavedChart.objects.filter(created_by=self.request.user).active()
    
    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

class SavedChartDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar un gráfico (borrado lógico)"""
    model = SavedChart
    template_name = 'charts/saved_chart_confirm_delete.html'
    success_url = reverse_lazy('saved_chart_list')
    
    def get_queryset(self):
        return SavedChart.objects.filter(created_by=self.request.user).active()
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.modified_by = request.user
        self.object.save()
        return redirect(self.success_url)

class DashboardListView(LoginRequiredMixin, ListView):
    """Vista para listar los dashboards del usuario"""
    template_name = 'charts/dashboard_list.html'
    context_object_name = 'dashboards'
    
    def get_queryset(self):
        return Dashboard.objects.filter(created_by=self.request.user).active()

class DashboardDetailView(LoginRequiredMixin, DetailView):
    """Vista para mostrar un dashboard con sus widgets"""
    model = Dashboard
    template_name = 'charts/dashboard_detail.html'
    context_object_name = 'dashboard'
    
    def get_queryset(self):
        return Dashboard.objects.filter(created_by=self.request.user).active()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar widgets al contexto
        context['widgets'] = DashboardWidget.objects.filter(
            dashboard=self.object
        ).active().select_related('saved_chart', 'saved_chart__chart_type')
        return context

class DashboardCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear un nuevo dashboard"""
    model = Dashboard
    form_class = DashboardForm
    template_name = 'charts/dashboard_form.html'
    success_url = reverse_lazy('dashboard_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # Verificar si está configurado como predeterminado, y desactivar cualquier predeterminado existente
        if form.cleaned_data.get('is_default', False):
            Dashboard.objects.filter(
                created_by=self.request.user, 
                is_default=True
            ).update(is_default=False)
        
        return super().form_valid(form)

class DashboardUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar un dashboard existente"""
    model = Dashboard
    form_class = DashboardForm
    template_name = 'charts/dashboard_form.html'
    
    def get_queryset(self):
        return Dashboard.objects.filter(created_by=self.request.user).active()
    
    def get_success_url(self):
        return reverse_lazy('dashboard_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        
        # Verificar si está configurado como predeterminado, y desactivar cualquier predeterminado existente
        if form.cleaned_data.get('is_default', False) and not self.object.is_default:
            Dashboard.objects.filter(
                created_by=self.request.user, 
                is_default=True
            ).update(is_default=False)
        
        return super().form_valid(form)

class DashboardDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar un dashboard (borrado lógico)"""
    model = Dashboard
    template_name = 'charts/dashboard_confirm_delete.html'
    success_url = reverse_lazy('dashboard_list')
    
    def get_queryset(self):
        return Dashboard.objects.filter(created_by=self.request.user).active()
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.modified_by = request.user
        self.object.save()
        return redirect(self.success_url)

class DashboardWidgetCreateView(LoginRequiredMixin, CreateView):
    """Vista para añadir un widget a un dashboard"""
    model = DashboardWidget
    form_class = DashboardWidgetForm
    template_name = 'charts/dashboard_widget_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Obtener el dashboard primero
        self.dashboard = get_object_or_404(
            Dashboard,
            pk=self.kwargs.get('dashboard_id'),
            created_by=request.user
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        initial['dashboard'] = self.dashboard
        return initial
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('dashboard_detail', kwargs={'pk': self.dashboard.pk})

class DashboardWidgetUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar un widget del dashboard"""
    model = DashboardWidget
    form_class = DashboardWidgetForm
    template_name = 'charts/dashboard_widget_form.html'
    
    def get_queryset(self):
        return DashboardWidget.objects.filter(
            dashboard__created_by=self.request.user
        ).active()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('dashboard_detail', kwargs={'pk': self.object.dashboard.pk})