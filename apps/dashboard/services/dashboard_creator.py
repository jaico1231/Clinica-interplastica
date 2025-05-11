from django.db.models import Sum, Count
from django.utils import timezone
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
import json
from datetime import timedelta

from apps.dashboard.models.dashboard_models import Dashboard, DashboardWidget, SavedChart, ChartType
from apps.sales.models import Sale, SaleItem, AccountReceivable, Payment

def create_admin_dashboards():
    """
    Crea dashboards genéricos para el grupo de administradores.
    Estos dashboards serán visibles para todos los usuarios que pertenezcan al grupo 'Administrador'.
    """
    # Obtener o crear el grupo de administradores
    admin_group, created = Group.objects.get_or_create(name='Administrador')
    
    # Obtener o crear tipos de gráficos necesarios
    chart_types = {
        'bar': ChartType.objects.get_or_create(
            code='bar',
            defaults={'name': 'Gráfico de Barras', 'icon_class': 'fa-bar-chart'}
        )[0],
        'line': ChartType.objects.get_or_create(
            code='line',
            defaults={'name': 'Gráfico de Línea', 'icon_class': 'fa-line-chart'}
        )[0],
        'pie': ChartType.objects.get_or_create(
            code='pie',
            defaults={'name': 'Gráfico Circular', 'icon_class': 'fa-pie-chart'}
        )[0],
        'doughnut': ChartType.objects.get_or_create(
            code='doughnut',
            defaults={'name': 'Gráfico de Dona', 'icon_class': 'fa-circle-o-notch'}
        )[0]
    }
    
    # Obtener content types para los modelos necesarios
    content_types = {
        'sale': ContentType.objects.get_for_model(Sale),
        'sale_item': ContentType.objects.get_for_model(SaleItem),
        'account_receivable': ContentType.objects.get_for_model(AccountReceivable),
        'payment': ContentType.objects.get_for_model(Payment)
    }
    
    with transaction.atomic():
        # Crear dashboard genérico de Ventas
        create_ventas_dashboard(admin_group, chart_types, content_types)
        
        # Crear dashboard genérico de Cartera
        create_cartera_dashboard(admin_group, chart_types, content_types)
        
        # Crear dashboard genérico de Rendimiento Mensual
        create_rendimiento_mensual_dashboard(admin_group, chart_types, content_types)
        
    return True

def create_ventas_dashboard(admin_group, chart_types, content_types):
    """
    Crea el dashboard genérico de Ventas para administradores
    """
    # Verificar si ya existe este dashboard para evitar duplicados
    if Dashboard.objects.filter(name="Ventas Diarias (Admin)", is_default=True).exists():
        return Dashboard.objects.get(name="Ventas Diarias (Admin)", is_default=True)
    
    # Crear el dashboard principal para el grupo admin
    dashboard = Dashboard.objects.create(
        name="Ventas Diarias (Admin)",
        description="Dashboard genérico de ventas diarias para administradores",
        is_default=True,
        layout_config={
            "columns": 12,
            "rowHeight": 150,
            "margin": 10
        }
    )
    
    # Asociar el dashboard con el grupo de administradores
    # Nota: Este campo no existe en el modelo actual, así que asumo una implementación
    # Si tu modelo Dashboard no tiene una relación con Group, deberás añadirla
    # dashboard.groups.add(admin_group)
    
    # 1. Gráfico: Total de Ventas por Día
    ventas_por_dia = SavedChart.objects.create(
        title="Total de Ventas por Día",
        description="Muestra el total monetario de ventas por día",
        chart_type=chart_types['bar'],
        model_content_type=content_types['sale'],
        x_axis_field="date",
        y_axis_field="total",
        filter_config=json.dumps({
            "status__in": ["confirmed", "paid"],
            "date__gte": "past_30_days"
        }),
        chart_config=json.dumps({
            "aggregate": "sum",
            "time_grouping": "day",
            "labels": {
                "x": "Fecha",
                "y": "Total (COP)"
            }
        }),
        color_scheme="blue",
        is_public=True
    )
    
    # Widget para el gráfico de ventas por día
    DashboardWidget.objects.create(
        dashboard=dashboard,
        saved_chart=ventas_por_dia,
        position_x=0,
        position_y=0,
        width=8,
        height=2,
        widget_config=json.dumps({
            "showTitle": True,
            "showLegend": True,
            "refreshInterval": 3600  # Actualizar cada hora
        })
    )
    
    # 2. Gráfico: Ventas por Método de Pago
    ventas_por_metodo = SavedChart.objects.create(
        title="Ventas por Método de Pago",
        description="Distribución de ventas según método de pago",
        chart_type=chart_types['pie'],
        model_content_type=content_types['sale'],
        x_axis_field="payment_method__name",
        y_axis_field="total",
        filter_config=json.dumps({
            "status__in": ["confirmed", "paid"],
            "date__gte": "past_30_days"
        }),
        chart_config=json.dumps({
            "aggregate": "sum",
            "labels": {
                "title": "Distribución por Método de Pago"
            }
        }),
        color_scheme="pastel",
        is_public=True
    )
    
    # Widget para el gráfico de método de pago
    DashboardWidget.objects.create(
        dashboard=dashboard,
        saved_chart=ventas_por_metodo,
        position_x=8,
        position_y=0,
        width=4,
        height=2,
        widget_config=json.dumps({
            "showTitle": True,
            "showLegend": True,
            "refreshInterval": 3600
        })
    )
    
    # 3. Gráfico: Servicios Más Vendidos
    servicios_mas_vendidos = SavedChart.objects.create(
        title="Servicios Más Vendidos",
        description="Servicios con mayor volumen de ventas",
        chart_type=chart_types['bar'],
        model_content_type=content_types['sale_item'],
        x_axis_field="service__name",
        y_axis_field="quantity",
        filter_config=json.dumps({
            "sale__status__in": ["confirmed", "paid"],
            "sale__date__gte": "past_30_days",
            "service__isnull": False
        }),
        chart_config=json.dumps({
            "aggregate": "sum",
            "limit": 10,
            "sort": "desc",
            "labels": {
                "x": "Servicio",
                "y": "Cantidad"
            }
        }),
        color_scheme="purple",
        is_public=True
    )
    
    # Widget para servicios más vendidos
    DashboardWidget.objects.create(
        dashboard=dashboard,
        saved_chart=servicios_mas_vendidos,
        position_x=0,
        position_y=2,
        width=12,
        height=2,
        widget_config=json.dumps({
            "showTitle": True,
            "showLegend": False,
            "refreshInterval": 3600
        })
    )
    
    return dashboard

def create_cartera_dashboard(admin_group, chart_types, content_types):
    """
    Crea el dashboard genérico de Cartera para administradores
    """
    # Verificar si ya existe este dashboard
    if Dashboard.objects.filter(name="Cartera (Admin)", is_default=True).exists():
        return Dashboard.objects.get(name="Cartera (Admin)", is_default=True)
    
    dashboard = Dashboard.objects.create(
        name="Cartera (Admin)",
        description="Dashboard genérico de cartera para administradores",
        is_default=True,
        layout_config={
            "columns": 12,
            "rowHeight": 150,
            "margin": 10
        }
    )
    
    # 1. Gráfico: Estado de Cuentas por Cobrar
    estado_cuentas = SavedChart.objects.create(
        title="Estado de Cuentas por Cobrar",
        description="Distribución de cuentas por cobrar según su estado",
        chart_type=chart_types['pie'],
        model_content_type=content_types['account_receivable'],
        x_axis_field="status",
        y_axis_field="pending_amount",
        filter_config=json.dumps({}),
        chart_config=json.dumps({
            "aggregate": "sum",
            "labels": {
                "pending": "Pendiente",
                "partial": "Pago Parcial",
                "paid": "Pagado",
                "cancelled": "Cancelado"
            }
        }),
        color_scheme="traffic_light",
        is_public=True
    )
    
    DashboardWidget.objects.create(
        dashboard=dashboard,
        saved_chart=estado_cuentas,
        position_x=0,
        position_y=0,
        width=6,
        height=2,
        widget_config=json.dumps({
            "showTitle": True,
            "showLegend": True,
            "refreshInterval": 3600
        })
    )
    
    # 2. Gráfico: Cuentas por Cobrar Vencidas
    cuentas_vencidas = SavedChart.objects.create(
        title="Cuentas por Cobrar Vencidas",
        description="Cuentas por cobrar vencidas agrupadas por días de retraso",
        chart_type=chart_types['bar'],
        model_content_type=content_types['account_receivable'],
        x_axis_field="due_date",
        y_axis_field="pending_amount",
        filter_config=json.dumps({
            "status__in": ["pending", "partial"],
            "due_date__lt": "today"
        }),
        chart_config=json.dumps({
            "aggregate": "sum",
            "time_grouping": "days_overdue",
            "ranges": [
                {"label": "1-7 días", "min": 1, "max": 7},
                {"label": "8-15 días", "min": 8, "max": 15},
                {"label": "16-30 días", "min": 16, "max": 30},
                {"label": "31-60 días", "min": 31, "max": 60},
                {"label": "Más de 60 días", "min": 61, "max": 9999}
            ],
            "labels": {
                "x": "Días de retraso",
                "y": "Monto pendiente (COP)"
            }
        }),
        color_scheme="red",
        is_public=True
    )
    
    DashboardWidget.objects.create(
        dashboard=dashboard,
        saved_chart=cuentas_vencidas,
        position_x=6,
        position_y=0,
        width=6,
        height=2,
        widget_config=json.dumps({
            "showTitle": True,
            "showLegend": False,
            "refreshInterval": 3600
        })
    )
    
    # 3. Gráfico: Pagos Recibidos por Día
    pagos_recibidos = SavedChart.objects.create(
        title="Pagos Recibidos por Día",
        description="Total de pagos recibidos diariamente",
        chart_type=chart_types['line'],
        model_content_type=content_types['payment'],
        x_axis_field="date",
        y_axis_field="amount",
        filter_config=json.dumps({
            "approved": True,
            "date__gte": "past_30_days"
        }),
        chart_config=json.dumps({
            "aggregate": "sum",
            "time_grouping": "day",
            "labels": {
                "x": "Fecha",
                "y": "Monto (COP)"
            }
        }),
        color_scheme="green",
        is_public=True
    )
    
    DashboardWidget.objects.create(
        dashboard=dashboard,
        saved_chart=pagos_recibidos,
        position_x=0,
        position_y=2,
        width=12,
        height=2,
        widget_config=json.dumps({
            "showTitle": True,
            "showLegend": False,
            "refreshInterval": 3600
        })
    )
    
    return dashboard

def create_rendimiento_mensual_dashboard(admin_group, chart_types, content_types):
    """
    Crea el dashboard genérico de Rendimiento Mensual para administradores
    """
    # Verificar si ya existe este dashboard
    if Dashboard.objects.filter(name="Rendimiento Mensual (Admin)", is_default=True).exists():
        return Dashboard.objects.get(name="Rendimiento Mensual (Admin)", is_default=True)
    
    dashboard = Dashboard.objects.create(
        name="Rendimiento Mensual (Admin)",
        description="Dashboard genérico de rendimiento mensual para administradores",
        is_default=True,
        layout_config={
            "columns": 12,
            "rowHeight": 150,
            "margin": 10
        }
    )
    
    # 1. Gráfico: Comparativa de Ventas por Mes
    comparativa_ventas = SavedChart.objects.create(
        title="Comparativa de Ventas Mensual",
        description="Compara las ventas de los últimos 6 meses",
        chart_type=chart_types['bar'],
        model_content_type=content_types['sale'],
        x_axis_field="date",
        y_axis_field="total",
        filter_config=json.dumps({
            "status__in": ["confirmed", "paid"],
            "date__gte": "past_180_days"
        }),
        chart_config=json.dumps({
            "aggregate": "sum",
            "time_grouping": "month",
            "labels": {
                "x": "Mes",
                "y": "Total Ventas (COP)"
            }
        }),
        color_scheme="blue",
        is_public=True
    )
    
    DashboardWidget.objects.create(
        dashboard=dashboard,
        saved_chart=comparativa_ventas,
        position_x=0,
        position_y=0,
        width=12,
        height=2,
        widget_config=json.dumps({
            "showTitle": True,
            "showLegend": False,
            "refreshInterval": 3600
        })
    )
    
    # 2. Gráfico: Top 10 Clientes por Volumen de Compra
    top_clientes = SavedChart.objects.create(
        title="Top 10 Clientes",
        description="Clientes con mayor volumen de compras",
        chart_type=chart_types['bar'],
        model_content_type=content_types['sale'],
        x_axis_field="patient__name",
        y_axis_field="total",
        filter_config=json.dumps({
            "status__in": ["confirmed", "paid"],
            "date__gte": "past_180_days"
        }),
        chart_config=json.dumps({
            "aggregate": "sum",
            "limit": 10,
            "sort": "desc",
            "labels": {
                "x": "Cliente",
                "y": "Total (COP)"
            }
        }),
        color_scheme="green",
        is_public=True
    )
    
    DashboardWidget.objects.create(
        dashboard=dashboard,
        saved_chart=top_clientes,
        position_x=0,
        position_y=2,
        width=6,
        height=2,
        widget_config=json.dumps({
            "showTitle": True,
            "showLegend": False,
            "refreshInterval": 3600
        })
    )
    
    # 3. Gráfico: Top 10 Médicos por Referidos
    top_medicos = SavedChart.objects.create(
        title="Top 10 Médicos por Referidos",
        description="Médicos con mayor volumen de pacientes referidos",
        chart_type=chart_types['bar'],
        model_content_type=content_types['sale'],
        x_axis_field="doctor__name",
        y_axis_field="total",
        filter_config=json.dumps({
            "status__in": ["confirmed", "paid"],
            "date__gte": "past_180_days",
            "doctor__isnull": False
        }),
        chart_config=json.dumps({
            "aggregate": "sum",
            "limit": 10,
            "sort": "desc",
            "labels": {
                "x": "Médico",
                "y": "Total (COP)"
            }
        }),
        color_scheme="purple",
        is_public=True
    )
    
    DashboardWidget.objects.create(
        dashboard=dashboard,
        saved_chart=top_medicos,
        position_x=6,
        position_y=2,
        width=6,
        height=2,
        widget_config=json.dumps({
            "showTitle": True,
            "showLegend": False,
            "refreshInterval": 3600
        })
    )
    
    return dashboard

# Función para aplicar permisos a los dashboards genéricos
def apply_admin_permissions_to_dashboards():
    """
    Asigna permisos al grupo de administradores para ver los dashboards genéricos
    Nota: Esta función depende de cómo estén implementados los permisos en tu aplicación
    """
    # Obtener el grupo de administradores
    try:
        admin_group = Group.objects.get(name='Administrador')
        
        # Obtener todos los dashboards genéricos
        admin_dashboards = Dashboard.objects.filter(
            name__contains='(Admin)',
            is_default=True
        )
        
        # Aquí debes implementar la lógica para asignar permisos
        # Esto dependerá de cómo manejas los permisos en tu aplicación
        # Por ejemplo, si usas un modelo de permisos personalizado:
        
        # from apps.dashboard.models.permission_models import DashboardPermission
        # for dashboard in admin_dashboards:
        #     DashboardPermission.objects.get_or_create(
        #         dashboard=dashboard,
        #         group=admin_group,
        #         defaults={
        #             'can_view': True,
        #             'can_edit': True
        #         }
        #     )
        
        return True
    except Group.DoesNotExist:
        print("El grupo Administrador no existe")
        return False