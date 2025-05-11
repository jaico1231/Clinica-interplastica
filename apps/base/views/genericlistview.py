# En apps/base/views/base_views.py (crear este archivo si no existe)

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

class OptimizedListView(ListView):
    """
    Base para todas las vistas de lista con optimizaciones de rendimiento.
    Elimina el registro de auditoría de visualizaciones y añade funcionalidad
    de búsqueda común.
    """
    paginate_by = 20  # Paginación por defecto
    search_fields = []  # Campos para búsqueda
    order_by = None  # Ordenamiento por defecto (puede ser string, list o tuple)
    exclude_search_fields = []  # Campos para búsqueda negativa
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Aplicar búsqueda si hay campos definidos
        search_term = self.request.GET.get('search', '')
        if search_term and self.search_fields:
            print(f"Buscando: '{search_term}' en campos: {self.search_fields}")

            filters = Q()
            for field in self.search_fields:
                filters |= Q(**{f"{field}__icontains": search_term})
            queryset = queryset.filter(filters)
        
        # Aplicar filtros adicionales desde parámetros GET
        for param, value in self.request.GET.items():
            if param.startswith('filter_') and value:
                filter_field = param.replace('filter_', '')
                # Manejar casos especiales para filtros de fecha y relaciones
                if filter_field.endswith('_date'):
                    # Usar __date si es un filtro de fecha (YYYY-MM-DD)
                    queryset = queryset.filter(**{f"{filter_field}__date": value})
                elif filter_field.endswith('_range'):
                    # Formato esperado: start_date,end_date
                    base_field = filter_field.replace('_range', '')
                    try:
                        start, end = value.split(',')
                        if start:
                            queryset = queryset.filter(**{f"{base_field}__gte": start})
                        if end:
                            queryset = queryset.filter(**{f"{base_field}__lte": end})
                    except ValueError:
                        pass  # Ignorar valores incorrectos
                else:
                    queryset = queryset.filter(**{filter_field: value})
        
        # Aplicar ordenamiento si está definido en la URL
        order_param = self.request.GET.get('order_by', '')
        if order_param:
            # Manejar múltiples campos de ordenamiento separados por comas
            if ',' in order_param:
                order_fields = [field.strip() for field in order_param.split(',')]
                queryset = queryset.order_by(*order_fields)
            else:
                queryset = queryset.order_by(order_param)
        # Ordenamiento por defecto definido en la clase
        elif self.order_by:
            # Si es string, usarlo directamente
            if isinstance(self.order_by, str):
                queryset = queryset.order_by(self.order_by)
            # Si es lista o tupla, desempaquetar los valores
            elif isinstance(self.order_by, (list, tuple)):
                queryset = queryset.order_by(*self.order_by)
        
        # Select related para optimizar consultas con relaciones frecuentes
        # Solo aplicar si existen estos campos
        select_related_fields = []
        if hasattr(self.model, 'owner'):
            select_related_fields.append('owner')
        if hasattr(self.model, 'created_by'):
            select_related_fields.append('created_by')
        
        if select_related_fields:
            queryset = queryset.select_related(*select_related_fields)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pasar los parámetros de búsqueda al contexto para mantener estado
        context['search_term'] = self.request.GET.get('search', '')
        
        # Pasar filtros actuales al contexto
        context['active_filters'] = {
            k.replace('filter_', ''): v 
            for k, v in self.request.GET.items() 
            if k.startswith('filter_') and v
        }
        
        # Pasar parámetro de ordenamiento
        context['current_order'] = self.request.GET.get('order_by', '')
        
        # Pasar campos de ordenamiento por defecto para la interfaz
        if self.order_by:
            if isinstance(self.order_by, str):
                context['default_order'] = self.order_by
            elif isinstance(self.order_by, (list, tuple)):
                context['default_order'] = ','.join(self.order_by)
        
        return context


class OptimizedSecureListView(LoginRequiredMixin, PermissionRequiredMixin, OptimizedListView):
    """
    Versión segura de la vista de lista optimizada que requiere autenticación y permisos.
    Incluye funcionalidades comunes para todas las vistas de lista seguras.
    """
    template_name = 'core/list.html'  # Template por defecto
    add_permission = None  # Permiso para añadir registros
    edit_permission = None  # Permiso para editar registros
    delete_permission = None  # Permiso para eliminar registros
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Datos básicos
        context['title'] = getattr(self, 'title', f'Listado de {self.model._meta.verbose_name_plural.title()}')
        context['entity'] = getattr(self, 'entity', self.model._meta.verbose_name.title())
        
        # URL de cancelación por defecto
        if not hasattr(context, 'cancel_url') and hasattr(self, 'success_url'):
            context['cancel_url'] = self.success_url
        
        # Configuración para toggle de estado activo/inactivo
        if hasattr(self.model, 'is_active'):
            context['use_toggle'] = True
            context['toggle_app_name'] = getattr(self, 'toggle_app_name', self.model._meta.app_label)
            context['toggle_model_name'] = getattr(self, 'toggle_model_name', self.model._meta.model_name)
            context['url_toggle'] = getattr(self, 'url_toggle', f'{self.model._meta.app_label}:toggle_active_status')
        
        # Permisos para botones de acción
        user = self.request.user
        
        # Verificar permisos para botones y acciones
        if self.add_permission:
            context['can_add'] = user.has_perm(self.add_permission)
        else:
            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            context['can_add'] = user.has_perm(f'{app_label}.add_{model_name}')
            
        if self.edit_permission:
            context['can_edit'] = user.has_perm(self.edit_permission)
        else:
            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            context['can_edit'] = user.has_perm(f'{app_label}.change_{model_name}')
            
        if self.delete_permission:
            context['can_delete'] = user.has_perm(self.delete_permission)
        else:
            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            context['can_delete'] = user.has_perm(f'{app_label}.delete_{model_name}')
        
        # Filtrar botones y acciones basados en permisos
        if 'Btn_Add' in context and not context['can_add']:
            context['Btn_Add'] = [btn for btn in context['Btn_Add'] if btn.get('name') != 'add']
            
        if 'actions' in context:
            actions = context['actions']
            if not context['can_edit']:
                actions = [action for action in actions if action.get('name') != 'edit']
            if not context['can_delete']:
                actions = [action for action in actions if action.get('name') not in ['del', 'delete']]
            context['actions'] = actions
            
        return context

    def get_queryset(self):
        """
        Opcionalmente filtrar resultados por permiso para ver solo registros propios.
        """
        queryset = super().get_queryset()
        
        # Si existe scope_queryset, aplicar restricciones adicionales
        if hasattr(self, 'scope_queryset'):
            queryset = self.scope_queryset(queryset)
            
        # Filtrar por owner si el usuario no es staff/superuser
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            # Si el modelo tiene campo owner, filtrar solo registros propios
            if hasattr(self.model, 'owner'):
                queryset = queryset.filter(owner=user)
                
        return queryset
        
    def scope_queryset(self, queryset):
        """
        Hook para que las subclases puedan implementar restricciones adicionales
        de acceso a los datos basadas en el usuario actual.
        """
        return queryset