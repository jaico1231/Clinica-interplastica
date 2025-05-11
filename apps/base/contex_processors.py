# config/context_processors.py
from django.conf import settings

def payments_enabled(request):
    """
    Context processor to make PAYMENTS_ENABLED setting available in templates
    """
    return {
        'PAYMENTS_ENABLED': getattr(settings, 'PAYMENTS_ENABLED', False)
    }