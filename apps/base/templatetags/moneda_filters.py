# myapp/templatetags/moneda_filters.py

from django import template
import locale

register = template.Library()

# Configura la localización para el formato monetario
locale.setlocale(locale.LC_ALL, '')

@register.filter(name='moneda')
def moneda(value):
    try:
        return locale.currency(value, grouping=True)
    except (TypeError, ValueError):
        return value
