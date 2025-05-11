from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.base.templatetags.menu_decorador import add_menu_name
# from apps.dashboard.views.dashboard_views import AddChartToDashboardView, ChartDeleteView, ChartTypeViewSet, DashboardHomeView, GetChartPreviewView, GetFieldDistributionView, GetModelFieldsView, SaveChartView, SavedChartListView, SavedChartDetailView, ChartBuilderView, DataReportListView, SavedChartViewSet, ToggleChartFavoriteView
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.dashboard.views.dashboard_views import (
    ChartTypeListView,
    ChartTypeViewSet,
    DashboardCreateView,
    DashboardDeleteView,
    DashboardDetailView,
    DashboardListView,
    DashboardUpdateView,
    DashboardViewSet,
    DashboardWidgetCreateView,
    DashboardWidgetUpdateView,
    DashboardWidgetViewSet,
    DataReportViewSet,
    SavedChartCreateView,
    SavedChartDeleteView,
    SavedChartListView,
    SavedChartUpdateView,
    SavedChartViewSet,
    available_models,
    chart_preview,
    model_fields,
    )
from apps.dashboard.views.dashboard_views_old import ChartBuilderView, DashboardHomeView, DataReportListView
# from apps.dashboard.views.dashboard_views_old import (
#     DashboardHomeView,
#     )

app_name = 'dashboard'
app_icon = 'dashboard'

# Configurar rutas para API REST
router = DefaultRouter()
router.register(r'chart-types', ChartTypeViewSet, basename='chart-type')
router.register(r'charts', SavedChartViewSet, basename='chart')
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'widgets', DashboardWidgetViewSet, basename='widget')
router.register(r'reports', DataReportViewSet, basename='report')

# Patrones de URL para vistas con plantillas
template_urlpatterns = [
    # Tipos de gráficos
    path('chart-types/', ChartTypeListView.as_view(), name='chart_type_list'),
    
    # Gráficos guardados
    path('charts/', SavedChartListView.as_view(), name='saved_chart_list'),
    path('charts/create/', SavedChartCreateView.as_view(), name='saved_chart_create'),
    path('charts/<int:pk>/edit/', SavedChartUpdateView.as_view(), name='saved_chart_update'),
    path('charts/<int:pk>/delete/', SavedChartDeleteView.as_view(), name='saved_chart_delete'),
    
    # Dashboards
    path('principal', login_required(add_menu_name('DASHBOARD','stacked_line_chart')(DashboardHomeView.as_view())), name='home'),
    path('charts/', login_required(add_menu_name('GRAFICOS','bar_chart')(SavedChartListView.as_view())), name='chart_list'),
    path('chart-builder/', login_required(add_menu_name('CREAR GRAFICO','add_circle')(ChartBuilderView.as_view())), name='chart_builder'),
    path('reports/', login_required(add_menu_name('INFORMES','document_scanner')(DataReportListView.as_view())), name='report_list'),    
    path('dashboards/', DashboardListView.as_view(), name='dashboard_list'),
    path('dashboards/create/', DashboardCreateView.as_view(), name='dashboard_create'),
    path('dashboards/<int:pk>/', DashboardDetailView.as_view(), name='dashboard_detail'),
    path('dashboards/<int:pk>/edit/', DashboardUpdateView.as_view(), name='dashboard_update'),
    path('dashboards/<int:pk>/delete/', DashboardDeleteView.as_view(), name='dashboard_delete'),
    
    # Widgets de dashboard
    path('dashboards/<int:dashboard_id>/widgets/add/', 
        DashboardWidgetCreateView.as_view(), name='dashboard_widget_create'),
    path('widgets/<int:pk>/edit/', 
        DashboardWidgetUpdateView.as_view(), name='dashboard_widget_update'),
]

# Patrones de URL para vistas basadas en funciones
utility_urlpatterns = [
    path('utils/model-fields/', model_fields, name='model_fields'),
    path('utils/available-models/', available_models, name='available_models'),
    path('utils/chart-preview/', chart_preview, name='chart_preview'),
]

# Combinar todos los patrones de URL
urlpatterns = [
    # Endpoints de API
    path('api/', include(router.urls)),
    
    # Vistas de utilidad basadas en funciones
    path('', include(utility_urlpatterns)),
    
    # Vistas basadas en plantillas
    path('', include(template_urlpatterns)),
]

# urlpatterns = [
#     # Vistas principales
#     path('principal', login_required(add_menu_name('DASHBOARD','stacked_line_chart')(DashboardHomeView.as_view())), name='home'),
#     path('charts/', login_required(add_menu_name('GRAFICOS','bar_chart')(SavedChartListView.as_view())), name='chart_list'),
#     path('charts/<int:pk>/', SavedChartDetailView.as_view(), name='chart_detail'),
#     path('chart-builder/', login_required(add_menu_name('CREAR GRAFICO','add_circle')(ChartBuilderView.as_view())), name='chart_builder'),
#     path('chart-builder/<int:pk>/', ChartBuilderView.as_view(), name='chart_edit'),
#     path('chart-delete/<int:pk>/', ChartDeleteView.as_view(), name='delete_chart'),
#     path('charts/toggle-favorite/', ToggleChartFavoriteView.as_view(), name='toggle_chart_favorite'),
#     # path('charts/toggle-favorite/', ToggleChartFavoriteView.as_view(), name='toggle_chart_favorite'),  
#     # APIs
#     path('api/save-chart/', SaveChartView.as_view(), name='save_chart'),
#     path('api/get-model-fields/', GetModelFieldsView.as_view(), name='get_model_fields'),
#     path('api/get-field-distribution/', GetFieldDistributionView.as_view(), name='get_field_distribution'),
#     path('api/get-chart-preview/', GetChartPreviewView.as_view(), name='get_chart_preview'),
#     path('api/add-chart-to-dashboard/', AddChartToDashboardView.as_view(), name='add_chart_to_dashboard'),

#     path('reports/', login_required(add_menu_name('INFORMES','document_scanner')(DataReportListView.as_view())), name='report_list'),    
    
#     # path('reports/create/', views.CreateReportView.as_view(), name='create_report'),
#     # path('reports/edit/<int:pk>/', views.EditReportView.as_view(), name='edit_report'),
#     # path('reports/view/<int:pk>/', views.ViewReportView.as_view(), name='view_report'),
#     # path('reports/delete/<int:pk>/', views.DeleteReportView.as_view(), name='delete_report'),
#     # path('reports/export/<int:pk>/', views.ExportReportView.as_view(), name='export_report'),
#     # path('reports/run/<int:pk>/', views.RunReportView.as_view(), name='run_report'),
#     # path('reports/schedule/<int:pk>/', views.ScheduleReportView.as_view(), name='schedule_report'),
# ]

