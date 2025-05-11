# # apps/surveys/templatetags/survey_tags.py
# from django import template
# from django.utils import timezone

# register = template.Library()

# @register.filter
# def get_item(dictionary, key):
#     """Get a value from a dictionary by key"""
#     return dictionary.get(key)

# @register.filter
# def contains(value, arg):
#     """Check if a value is in a list or queryset"""
#     return arg in value

# @register.filter
# def yesno(value, arg=None):
#     """
#     Given a string mapping values for true, false and (optionally) None,
#     returns one of those strings according to the value:

#     ==========  ======================  ==================================
#     Value       Argument                Outputs
#     ==========  ======================  ==================================
#     ``True``    ``"yeah,no,maybe"``     ``yeah``
#     ``False``   ``"yeah,no,maybe"``     ``no``
#     ``None``    ``"yeah,no,maybe"``     ``maybe``
#     ``None``    ``"yeah,no"``           ``"no"`` (converts None to False)
#     ==========  ======================  ==================================
#     """
#     if arg is None:
#         arg = "Sí,No"
#     bits = arg.split(',')
#     if len(bits) < 2:
#         return value  # Invalid arg.
#     try:
#         yes, no, maybe = bits
#     except ValueError:
#         # Unpack list of wrong size (no "maybe" value provided).
#         yes, no = bits
#         maybe = no
#     if value is None:
#         return maybe
#     if value:
#         return yes
#     return no