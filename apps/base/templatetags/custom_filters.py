from django import template
import json
register = template.Library()

@register.filter
def getattr_filter(obj, attr):
    return getattr(obj, attr, '')


# para auditoria
@register.filter
def get_item(dictionary, key):
    """
    Obtiene un valor de un diccionario por su clave.
    Maneja casos donde el input no es un diccionario.
    """
    # Verificar que dictionary sea realmente un diccionario o similar
    if dictionary is None:
        return None
    
    # Si es un string, intentar convertirlo a dict (si es JSON)
    if isinstance(dictionary, str):
        try:
            import json
            dictionary = json.loads(dictionary)
        except:
            # Si no se puede convertir, devolver None
            return None
    
    # Si es un dict normal
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    
    # Si es un objeto que permite acceso por índice
    try:
        return dictionary[key]
    except (KeyError, TypeError, IndexError):
        return None
    
    # def get_item(dictionary, key):
#     """
#     Obtiene un valor de un diccionario por su clave.
#     Usado para acceder a los datos de auditoría en el template.
#     """
#     return dictionary.get(key)
# prueba de filtro mejorado

@register.filter
def json_pretty(value):
    """
    Formatea un objeto JSON para mostrar en el template.
    """
    if value is None:
        return "-"
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)

@register.filter
def highlight_diff(old_value, new_value):
    """
    Resalta las diferencias entre dos valores.
    """
    if old_value == new_value:
        return new_value
    
    old_str = str(old_value)
    new_str = str(new_value)
    
    return f'<span class="diff-changed">{old_str} → {new_str}</span>'

@register.filter
def sub(value, arg):
    """Resta el valor de arg a value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''