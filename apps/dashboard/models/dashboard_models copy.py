from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings
from apps.base.models.basemodel import BaseModel, CompleteModel  # Importar tus modelos base
import json

class ChartType(BaseModel):  # Hereda de BaseModel
    """Tipos de gráficos disponibles en el dashboard"""
    name = models.CharField(_("Nombre"), max_length=50)
    code = models.CharField(_("Código"), max_length=20, unique=True)
    description = models.TextField(_("Descripción"), blank=True, null=True)
    icon_class = models.CharField(_("Clase de icono"), max_length=50, blank=True, null=True)
    
    class Meta(BaseModel.Meta):  # Hereda la Meta del BaseModel
        verbose_name = _("Tipo de gráfico")
        verbose_name_plural = _("Tipos de gráficos")
    
    def __str__(self):
        return self.name

class SavedChart(CompleteModel):  # Hereda de CompleteModel para tener auditoría y borrado lógico
    """Gráficos guardados por los usuarios"""
    title = models.CharField(_("Título"), max_length=100)
    description = models.TextField(_("Descripción"), blank=True, null=True)
    chart_type = models.ForeignKey(ChartType, on_delete=models.CASCADE, verbose_name=_("Tipo de gráfico"))
    model_content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        verbose_name=_("Modelo"),
        help_text=_("El modelo de datos que se usa para este gráfico")
    )
    x_axis_field = models.CharField(_("Campo eje X"), max_length=100)
    y_axis_field = models.CharField(_("Campo eje Y"), max_length=100)
    filter_config = models.JSONField(_("Configuración de filtros"), blank=True, null=True)
    chart_config = models.JSONField(_("Configuración del gráfico"), blank=True, null=True)
    color_scheme = models.CharField(_("Esquema de colores"), max_length=50, blank=True, null=True)
    is_public = models.BooleanField(_("Es público"), default=False)
    is_favorite = models.BooleanField(_("Es favorito"), default=False)
    
    class Meta(CompleteModel.Meta):  # Hereda la Meta del CompleteModel
        verbose_name = _("Gráfico guardado")
        verbose_name_plural = _("Gráficos guardados")
    
    def __str__(self):
        return self.title
    
    # El resto de métodos se mantienen iguales...

class Dashboard(CompleteModel):  # Hereda de CompleteModel
    """Dashboard personalizable por el usuario"""
    name = models.CharField(_("Nombre"), max_length=100)
    description = models.TextField(_("Descripción"), blank=True, null=True)
    layout_config = models.JSONField(_("Configuración de diseño"), blank=True, null=True)
    is_default = models.BooleanField(_("Es predeterminado"), default=False)
    
    class Meta(CompleteModel.Meta):  # Hereda la Meta del CompleteModel
        verbose_name = _("Dashboard")
        verbose_name_plural = _("Dashboards")
    
    def __str__(self):
        return self.name

class DashboardWidget(CompleteModel):  # Hereda de CompleteModel
    """Widget dentro de un dashboard"""
    dashboard = models.ForeignKey(
        Dashboard, 
        on_delete=models.CASCADE,
        related_name="widgets",
        verbose_name=_("Dashboard")
    )
    saved_chart = models.ForeignKey(
        SavedChart,
        on_delete=models.CASCADE,
        verbose_name=_("Gráfico guardado")
    )
    position_x = models.IntegerField(_("Posición X"), default=0)
    position_y = models.IntegerField(_("Posición Y"), default=0)
    width = models.IntegerField(_("Ancho"), default=4)
    height = models.IntegerField(_("Alto"), default=3)
    widget_config = models.JSONField(_("Configuración del widget"), blank=True, null=True)
    
    class Meta(CompleteModel.Meta):  # Hereda la Meta del CompleteModel
        verbose_name = _("Widget de dashboard")
        verbose_name_plural = _("Widgets de dashboard")
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.dashboard.name} - {self.saved_chart.title}"

class DataReport(CompleteModel):  # Hereda de CompleteModel
    """Informes de datos generados por los usuarios"""
    title = models.CharField(_("Título"), max_length=100)
    description = models.TextField(_("Descripción"), blank=True, null=True)
    models_included = models.JSONField(_("Modelos incluidos"), blank=True, null=True)
    report_config = models.JSONField(_("Configuración del informe"), blank=True, null=True)
    last_generated = models.DateTimeField(_("Última generación"), blank=True, null=True)
    
    class Meta(CompleteModel.Meta):  # Hereda la Meta del CompleteModel
        verbose_name = _("Informe de datos")
        verbose_name_plural = _("Informes de datos")
    
    def __str__(self):
        return self.title
    
    # El resto de métodos se mantienen iguales...