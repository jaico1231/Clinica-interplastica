from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def getattribute(obj, attr_name):
    """
    Permite acceder a atributos de un objeto desde una plantilla usando una cadena.
    Útil para las plantillas genéricas donde necesitamos acceso dinámico a los campos.
    
    Uso: {{ objeto|getattribute:"nombre_campo" }}
    También permite acceso a métodos: {{ objeto|getattribute:"get_absolute_url" }}
    """
    try:
        attr = getattr(obj, attr_name)
        if callable(attr):
            return attr()
        return attr
    except (AttributeError, TypeError):
        return ""

@register.filter
def yesno_bootstrap(value):
    """
    Convierte un valor booleano en un icono de Bootstrap.
    
    Uso: {{ objeto.is_active|yesno_bootstrap }}
    """
    if value:
        return mark_safe('<span class="badge bg-success"><i class="fas fa-check"></i> Sí</span>')
    else:
        return mark_safe('<span class="badge bg-danger"><i class="fas fa-times"></i> No</span>')

@register.filter
def format_currency(value):
    """
    Formatea un valor como moneda.
    
    Uso: {{ objeto.precio|format_currency }}
    """
    if value is None:
        return "-"
    try:
        return "${:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return value