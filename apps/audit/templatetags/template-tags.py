# # En apps/audit/templatetags/audit_filters.py
# from django import template
# import json

# register = template.Library()

# @register.filter
# def get_item(dictionary, key):
#     """
#     Obtiene un valor de un diccionario por su clave.
#     Usado para acceder a los datos de auditoría en el template.
#     """
#     return dictionary.get(key)

# @register.filter
# def json_pretty(value):
#     """
#     Formatea un objeto JSON para mostrar en el template.
#     """
#     if value is None:
#         return "-"
#     try:
#         return json.dumps(value, indent=2, ensure_ascii=False)
#     except (TypeError, ValueError):
#         return str(value)

# @register.filter
# def highlight_diff(old_value, new_value):
#     """
#     Resalta las diferencias entre dos valores.
#     """
#     if old_value == new_value:
#         return new_value
    
#     old_str = str(old_value)
#     new_str = str(new_value)
    
#     return f'<span class="diff-changed">{old_str} → {new_str}</span>'
