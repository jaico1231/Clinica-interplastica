from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.base.templatetags.menu_decorador import add_menu_name
from apps.dashboard.views.dashboard_views import AddChartToDashboardView, ChartDeleteView, DashboardHomeView, GetChartPreviewView, GetFieldDistributionView, GetModelFieldsView, SaveChartView, SavedChartListView, SavedChartDetailView, ChartBuilderView, DataReportListView, ToggleChartFavoriteView

app_name = 'dashboard'
app_icon = 'dashboard'

urlpatterns = [
    # Vistas principales
    path('principal', login_required(add_menu_name('DASHBOARD','stacked_line_chart')(DashboardHomeView.as_view())), name='home'),
    path('charts/', login_required(add_menu_name('GRAFICOS','bar_chart')(SavedChartListView.as_view())), name='chart_list'),
    path('charts/<int:pk>/', SavedChartDetailView.as_view(), name='chart_detail'),
    path('chart-builder/', login_required(add_menu_name('CREAR GRAFICO','add_circle')(ChartBuilderView.as_view())), name='chart_builder'),
    path('chart-builder/<int:pk>/', ChartBuilderView.as_view(), name='chart_edit'),
    path('chart-delete/<int:pk>/', ChartDeleteView.as_view(), name='delete_chart'),
    path('charts/toggle-favorite/', ToggleChartFavoriteView.as_view(), name='toggle_chart_favorite'),
    # path('charts/toggle-favorite/', ToggleChartFavoriteView.as_view(), name='toggle_chart_favorite'),  
    # APIs
    path('api/save-chart/', SaveChartView.as_view(), name='save_chart'),
    path('api/get-model-fields/', GetModelFieldsView.as_view(), name='get_model_fields'),
    path('api/get-field-distribution/', GetFieldDistributionView.as_view(), name='get_field_distribution'),
    path('api/get-chart-preview/', GetChartPreviewView.as_view(), name='get_chart_preview'),
    path('api/add-chart-to-dashboard/', AddChartToDashboardView.as_view(), name='add_chart_to_dashboard'),

    path('reports/', login_required(add_menu_name('INFORMES','document_scanner')(DataReportListView.as_view())), name='report_list'),    
    
    # path('reports/create/', views.CreateReportView.as_view(), name='create_report'),
    # path('reports/edit/<int:pk>/', views.EditReportView.as_view(), name='edit_report'),
    # path('reports/view/<int:pk>/', views.ViewReportView.as_view(), name='view_report'),
    # path('reports/delete/<int:pk>/', views.DeleteReportView.as_view(), name='delete_report'),
    # path('reports/export/<int:pk>/', views.ExportReportView.as_view(), name='export_report'),
    # path('reports/run/<int:pk>/', views.RunReportView.as_view(), name='run_report'),
    # path('reports/schedule/<int:pk>/', views.ScheduleReportView.as_view(), name='schedule_report'),
]

