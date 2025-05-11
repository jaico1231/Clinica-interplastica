from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views import View

class GenericToggleActiveStatusView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista genérica para activar/desactivar cualquier modelo con campo is_active
    Parámetros esperados en las URL:
    - app_name: Nombre de la aplicación del modelo
    - model_name: Nombre del modelo
    - pk: ID del objeto
    
    Ejemplo de URL: /toggle-status/base/user/123/
    """
    
    def get_permission_required(self):
        """Determina dinámicamente el permiso requerido basado en el modelo"""
        app_name = self.kwargs.get('app_name')
        model_name = self.kwargs.get('model_name')
        return [f'{app_name}.change_{model_name}']
    
    def post(self, request, app_name, model_name, pk):
        try:
            # Obtener el modelo dinámicamente
            model = apps.get_model(app_name, model_name)
            
            # Obtener el objeto
            obj = get_object_or_404(model, pk=pk)
            
            # Verificar si existe el campo is_active
            if not hasattr(obj, 'is_active'):
                return JsonResponse({
                    'success': False,
                    'message': _('El modelo no tiene campo is_active')
                }, status=400)
            
            # Reglas específicas para ciertos modelos
            special_validations = getattr(self, f'validate_{model_name}', None)
            if special_validations:
                validation_result = special_validations(request, obj)
                if validation_result:
                    return validation_result
            
            # Cambiar estado
            obj.is_active = not obj.is_active
            obj.save()
            
            # Obtener el nombre para mostrar
            display_name = getattr(obj, 'get_display_name', lambda: str(obj))()
            if callable(display_name):
                display_name = display_name()
            
            status_msg = _("activado") if obj.is_active else _("desactivado")
            
            return JsonResponse({
                'success': True,
                'is_active': obj.is_active,
                'message': _("{} {} correctamente").format(display_name, status_msg)
            })
        except LookupError:
            return JsonResponse({
                'success': False,
                'message': _("Modelo no encontrado: {}.{}").format(app_name, model_name)
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': _("Error: {}").format(str(e))
            }, status=500)
    
    # Métodos de validación específicos por modelo
    def validate_user(self, request, user):
        """Validaciones específicas para el modelo User"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if user.is_superuser and user.username == 'admin':
            return JsonResponse({
                'success': False,
                'message': _('No se puede desactivar al administrador principal')
            }, status=400)
            
        if user == request.user:
            return JsonResponse({
                'success': False,
                'message': _('No puedes desactivarte a ti mismo')
            }, status=400)
        
        return None  # Continuar con el proceso normal
    
def add_toggle_context(context, model):
    """Añade el contexto necesario para el toggle de estado si el modelo tiene is_active."""
    if hasattr(model, 'is_active'):
        context['use_toggle'] = True
        context['url_toggle'] = 'configuracion:toggle_active_status'
        context['toggle_app_name'] = model._meta.app_label
        context['toggle_model_name'] = model._meta.model_name
    return context