from rest_framework import serializers

from apps.dashboard.models.dashboard_models import (
    ChartType, 
    SavedChart, 
    Dashboard, 
    DashboardWidget, 
    DataReport
    )
# from .models import ChartType, SavedChart, Dashboard, DashboardWidget, DataReport

class ChartTypeSerializer(serializers.ModelSerializer):
    """Serializador para tipos de gráficos"""
    
    class Meta:
        model = ChartType
        fields = ['id', 'name', 'code', 'description', 'icon_class']

class SavedChartSerializer(serializers.ModelSerializer):
    """Serializador para gráficos guardados"""
    chart_type_name = serializers.ReadOnlyField(source='chart_type.name')
    chart_type_code = serializers.ReadOnlyField(source='chart_type.code')
    model_name = serializers.ReadOnlyField(source='model_content_type.model')
    app_label = serializers.ReadOnlyField(source='model_content_type.app_label')
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = SavedChart
        fields = [
            'id', 'title', 'description', 'chart_type', 'chart_type_name',
            'chart_type_code', 'model_content_type', 'model_name', 'app_label',
            'x_axis_field', 'y_axis_field', 'filter_config', 'chart_config',
            'color_scheme', 'is_public', 'is_favorite', 'created_by_username',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['created_at', 'modified_at']

    def to_representation(self, instance):
        """Agrega formato adicional de representación si es necesario"""
        rep = super().to_representation(instance)
        # Si necesitamos formatear campos adicionales, lo haríamos aquí
        return rep

class DashboardWidgetSerializer(serializers.ModelSerializer):
    """Serializador para widgets de dashboard"""
    chart_title = serializers.ReadOnlyField(source='saved_chart.title')
    chart_type = serializers.ReadOnlyField(source='saved_chart.chart_type.code')
    
    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'dashboard', 'saved_chart', 'chart_title', 'chart_type',
            'position_x', 'position_y', 'width', 'height', 'widget_config',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['created_at', 'modified_at']

class DashboardSerializer(serializers.ModelSerializer):
    """Serializador para dashboards"""
    widgets = DashboardWidgetSerializer(many=True, read_only=True)
    widget_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description', 'layout_config', 'is_default',
            'created_at', 'modified_at', 'widgets', 'widget_count'
        ]
        read_only_fields = ['created_at', 'modified_at', 'widgets', 'widget_count']
    
    def get_widget_count(self, obj):
        """Obtiene el número de widgets activos en el dashboard"""
        return obj.widgets.filter(is_active=True).count()

class DataReportSerializer(serializers.ModelSerializer):
    """Serializador para informes de datos"""
    is_generated = serializers.SerializerMethodField()
    
    class Meta:
        model = DataReport
        fields = [
            'id', 'title', 'description', 'models_included', 'report_config',
            'last_generated', 'created_at', 'modified_at', 'is_generated'
        ]
        read_only_fields = ['last_generated', 'created_at', 'modified_at', 'is_generated']
    
    def get_is_generated(self, obj):
        """Determina si el informe ha sido generado alguna vez"""
        return obj.last_generated is not None