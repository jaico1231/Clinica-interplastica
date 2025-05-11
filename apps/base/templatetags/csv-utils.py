# Crear este archivo en yourapp/templatetags/csv_utils.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtiene un elemento de un diccionario por su clave"""
    if dictionary is None:
        return None
    return dictionary.get(key)
