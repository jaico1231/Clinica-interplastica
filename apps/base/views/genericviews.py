# genericviews.py
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.base.models.support import City, State

# Vista para cargar estados según el país seleccionado (para selectores dependientes)
class LoadStatesView(LoginRequiredMixin, View):
    """
    Vista para cargar estados/departamentos según el país seleccionado
    """
    def get(self, request):
        country_id = request.GET.get('country_id')
        if not country_id:
            return JsonResponse({'error': 'No se proporcionó ID de país'}, status=400)
            
        states = State.objects.filter(country_id=country_id).values('id', 'name')
        return JsonResponse(list(states), safe=False)

# Vista para cargar ciudades según el estado seleccionado (para selectores dependientes)
class LoadCitiesView(LoginRequiredMixin, View):
    """
    Vista para cargar ciudades según el estado/departamento seleccionado
    """
    def get(self, request):
        state_id = request.GET.get('state_id')
        if not state_id:
            return JsonResponse({'error': 'No se proporcionó ID de departamento'}, status=400)
            
        cities = City.objects.filter(state_id=state_id).values('id', 'name')
        return JsonResponse(list(cities), safe=False)
    """Vista genérica para ver detalles de un registro"""
    
    def get_template_names(self):
        """Determina la plantilla a usar"""
        if self.template_name:
            return [self.template_name]
            
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        
        return [
            f"{app_label}/{model_name}_detail.html",
            f"{app_label}/generic_detail.html",
            "core/generic_detail.html"
        ]
    
    def get_context_data(self, **kwargs):
        """Agrega información para crear botones de acción"""
        context = super().get_context_data(**kwargs)
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        
        # Añadir URLs para acciones CRUD
        context.update({
            'list_url': f"{app_label}:{model_name}_list",
            'update_url': f"{app_label}:{model_name}_update",
            'delete_url': f"{app_label}:{model_name}_delete",
        })
        
        return context