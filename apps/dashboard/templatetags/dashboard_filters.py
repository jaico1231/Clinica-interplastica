from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtro personalizado para acceder a elementos de un diccionario por clave.
    Permite usar dictionary.get_item:key en las plantillas.
    """
    if dictionary is None:
        return None
    
    # Si es un dict normal
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    
    # Si es un objeto que permite acceso por índice
    try:
        return dictionary[key]
    except (KeyError, TypeError, IndexError):
        return None