# apps/base/models/middleware.py
from threading import local

# Definir _thread_locals a nivel de módulo
_thread_locals = local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Limpiar el storage al inicio de cada solicitud
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
            
        # Almacenar el usuario actual
        if hasattr(request, 'user') and request.user.is_authenticated:
            _thread_locals.user = request.user
            
        response = self.get_response(request)
        return response