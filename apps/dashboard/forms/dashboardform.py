from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from apps.dashboard.models.dashboard_models import (
    SavedChart,
    Dashboard,
    DashboardWidget,
    ChartType,
    DataReport
    )

# from .models import ChartType, SavedChart, Dashboard, DashboardWidget, DataReport

class SavedChartForm(forms.ModelForm):
    """Formulario para crear/editar gráficos guardados"""
    
    class Meta:
        model = SavedChart
        fields = [
            'title', 'description', 'chart_type', 'model_content_type',
            'x_axis_field', 'y_axis_field', 'filter_config', 'chart_config',
            'color_scheme', 'is_public', 'is_favorite'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'filter_config': forms.HiddenInput(),
            'chart_config': forms.HiddenInput(),
            'x_axis_field': forms.Select(attrs={'class': 'form-control'}),
            'y_axis_field': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'color_scheme': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limitar tipos de gráficos a los activos
        self.fields['chart_type'].queryset = ChartType.objects.all()
        self.fields['chart_type'].widget.attrs.update({'class': 'form-control'})
        
        # Para content types, podríamos querer limitar a ciertos modelos
        self.fields['model_content_type'].queryset = ContentType.objects.all().order_by('app_label', 'model')
        self.fields['model_content_type'].widget.attrs.update({'class': 'form-control'})
        
        # Para x_axis_field e y_axis_field, inicialmente usamos campos de texto
        # En una implementación real, estos se poblarían dinámicamente basados en el modelo seleccionado
        self.fields['x_axis_field'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['y_axis_field'].widget = forms.TextInput(attrs={'class': 'form-control'})
        
        # Opciones adicionales para y_axis_field (para incluir agregaciones como "count")
        self.fields['y_axis_field'].help_text = _('Puede ser un campo del modelo o "count" para contar registros')
        
        # Añadir clases para checkboxes
        self.fields['is_public'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['is_favorite'].widget.attrs.update({'class': 'form-check-input'})

    def clean(self):
        cleaned_data = super().clean()
        model_content_type = cleaned_data.get('model_content_type')
        x_axis_field = cleaned_data.get('x_axis_field')
        y_axis_field = cleaned_data.get('y_axis_field')
        
        if model_content_type and x_axis_field:
            model_class = model_content_type.model_class()
            if not model_class:
                self.add_error('model_content_type', _('Modelo inválido'))
            else:
                # Validar que x_axis_field exista en el modelo
                if not hasattr(model_class, x_axis_field):
                    self.add_error('x_axis_field', _('El campo no existe en el modelo seleccionado'))
                
                # Validar y_axis_field solo si no es "count"
                if y_axis_field and y_axis_field != "count" and not hasattr(model_class, y_axis_field):
                    self.add_error('y_axis_field', _('El campo no existe en el modelo seleccionado'))
        
        return cleaned_data

class DashboardForm(forms.ModelForm):
    """Formulario para crear/editar dashboards"""
    
    class Meta:
        model = Dashboard
        fields = ['name', 'description', 'layout_config', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'layout_config': forms.HiddenInput(),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DashboardWidgetForm(forms.ModelForm):
    """Formulario para añadir/editar widgets de dashboard"""
    
    class Meta:
        model = DashboardWidget
        fields = [
            'dashboard', 'saved_chart', 'position_x', 'position_y',
            'width', 'height', 'widget_config'
        ]
        widgets = {
            'widget_config': forms.HiddenInput(),
            'position_x': forms.HiddenInput(),
            'position_y': forms.HiddenInput(),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Limitar dashboards a los creados por el usuario
            self.fields['dashboard'].queryset = Dashboard.objects.filter(
                created_by=user
            ).active()
            self.fields['dashboard'].widget.attrs.update({'class': 'form-control'})
            
            # Limitar gráficos a los creados por el usuario o públicos
            self.fields['saved_chart'].queryset = SavedChart.objects.filter(
                Q(created_by=user) | Q(is_public=True)
            ).active()
            self.fields['saved_chart'].widget.attrs.update({'class': 'form-control'})
        
        # Ayuda para dimensiones
        self.fields['width'].help_text = _('Ancho del widget (1-12, donde 12 es el ancho completo)')
        self.fields['height'].help_text = _('Alto del widget en unidades de cuadrícula')

class DataReportForm(forms.ModelForm):
    """Formulario para crear/editar informes de datos"""
    
    class Meta:
        model = DataReport
        fields = ['title', 'description', 'models_included', 'report_config']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'models_included': forms.HiddenInput(),
            'report_config': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Inicializar campos JSON con valores vacíos si son nuevos
        if not self.instance.pk:
            self.initial['models_included'] = '[]'
            self.initial['report_config'] = '{}'

class ChartFilterForm(forms.Form):
    """Formulario para filtrar la lista de gráficos"""
    chart_type = forms.ModelChoiceField(
        queryset=ChartType.objects.all(),
        required=False,
        empty_label=_("Todos los tipos"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_public = forms.BooleanField(
        required=False,
        label=_("Solo públicos"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_favorite = forms.BooleanField(
        required=False,
        label=_("Solo favoritos"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    search = forms.CharField(
        required=False,
        label=_("Buscar"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Buscar por título o descripción")
        })
    )