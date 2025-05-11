# middleware.py
from apps.audit.signals import thread_local

class AuditMiddleware:
    """
    Middleware para capturar el usuario actual y la solicitud para el registro de auditoría
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Almacenar el usuario y la solicitud en la variable local de thread
        if hasattr(request, 'user') and request.user.is_authenticated:
            thread_local.request_user = request.user
        else:
            # Si no hay usuario autenticado, eliminar si existe previamente
            if hasattr(thread_local, 'request_user'):
                del thread_local.request_user
                
        # Almacenar la solicitud para acceder a información como IP, user-agent, etc.
        thread_local.request = request
        
        # Procesar la solicitud
        response = self.get_response(request)
        
        # Limpiar después de procesar
        if hasattr(thread_local, 'request'):
            del thread_local.request
            
        return response