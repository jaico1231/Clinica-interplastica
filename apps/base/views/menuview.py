from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
import json

# Importamos el modelo AuditLog para registrar acciones específicas
from apps.audit.models import AuditLog
from apps.base.forms.menuform import MenuForm, MenuItemForm
from apps.base.models.menu import Menu, MenuItem
from apps.base.views.genericToggleIs_active import add_toggle_context
from apps.base.views.genericlistview import OptimizedSecureListView

class ListMenuView(OptimizedSecureListView):
    """
    Vista optimizada para listar menús con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'base.view_menu'
    model = Menu
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['name', 'icon']
    # Ordenamiento por defecto
    order_by = ('name',)
    
    # Atributos específicos
    title = 'Menu'
    entity = 'configuracion'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Registrar la acción de visualización de lista en la auditoría
        AuditLog.objects.create(
            user=self.request.user,
            action='VIEW',
            content_type=ContentType.objects.get_for_model(Menu),
            table_name=Menu._meta.db_table,
            description=f"Visualización de lista de menús"
        )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['NOMBRE', 'ICONO']
        context['fields'] = ['name', 'icon']
        
        # Configuración de acciones
        context['actions'] = [
            {
                'name': 'edit',
                'icon': 'edit',
                'label': 'Editar',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'configuracion:menu_edit',
                'modal': True
            }
        ]
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('configuracion:menu')
        
        # Configuración para toggle
        if hasattr(self.model, 'is_active'):
            context['use_toggle'] = True
            context['url_toggle'] = 'configuracion:toggle_active_status'
            # Pasar información adicional para la URL genérica
            context['toggle_app_name'] = self.model._meta.app_label
            context['toggle_model_name'] = self.model._meta.model_name
        
        return context

class MenuCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'base.add_menu'
    model = Menu
    template_name = 'core/form.html'
    form_class = MenuForm
    success_url = reverse_lazy('configuracion:menu')  # Corregido: debe ser configuracion:menu
    success_message = "Menú creado con éxito"

    def form_valid(self, form):
        form.instance.group = self.request.user.groups.first()
        messages.success(self.request, self.success_message)
        
        # La auditoría de creación se realizará automáticamente mediante las señales
        # No es necesario registrarla manualmente aquí
        
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Menu'
        context['entity'] = 'configuracion'  # Corregido: debe ser configuracion
        context['action'] = 'add'
        return context

class MenuUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'base.change_menu'  # Corregido: debe ser base.change_menu
    model = Menu
    template_name = 'core/form.html'  # Corregido: debe ser core/form.html
    form_class = MenuForm
    success_message = "Menú actualizado con éxito"
        
    def get_success_url(self):
        if self.request.headers.get('Accept') == 'application/json/html':
            return JsonResponse({'success': True, 'message': self.success_message})
        else:
            return reverse_lazy('configuracion:menu')  # Corregido: debe ser configuracion:menu
        
    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        # La auditoría de actualización se realizará automáticamente mediante las señales
        # No es necesario registrarla manualmente aquí
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Menu'
        context['entity'] = 'configuracion'  # Corregido: debe ser configuracion
        context['action'] = 'edit'
        return context

class MenuItemListView(OptimizedSecureListView):
    """
    Vista optimizada para listar items de menú con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'base.view_menuitem'  # Asumiendo que este es el permiso correcto
    model = MenuItem
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['menu__name', 'name', 'url_name', 'icon']
    # Ordenamiento por defecto
    order_by = ('menu__name', 'name')
    
    # Atributos específicos
    title = 'Menu Items'
    entity = 'configuracion'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Se puede agregar aquí cualquier filtro personalizado como en ListMenuView
        # Por ejemplo, filtrar por menú específico si se proporciona en la URL
        menu_id = self.request.GET.get('menu_id')
        if menu_id:
            queryset = queryset.filter(menu_id=menu_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['MENU', 'NOMBRE', 'URL', 'ICONO']
        context['fields'] = ['menu', 'name', 'url_name', 'icon']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': 'Agregar',
                'icon': 'add',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'configuracion:menuitem_create',
                'modal': True
            }
        ]
        
        context['actions'] = [
            {
                'name': 'edit',
                'icon': 'edit',
                'label': 'Editar',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'configuracion:menuitem_edit',
                'modal': True
            }
        ]
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('configuracion:menu')
        
        # Configuración para toggle usando la función existente
        # Reemplazamos la función add_toggle_context por la configuración directa
        if hasattr(self.model, 'is_active'):
            context['use_toggle'] = True
            context['url_toggle'] = 'configuracion:toggle_active_status'
            context['toggle_app_name'] = self.model._meta.app_label
            context['toggle_model_name'] = self.model._meta.model_name
        
        return context
        

class MenuItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'base.add_menuitem'  # Corregido: debe ser base.add_menuitem
    model = MenuItem
    template_name = 'core/create.html'  # Corregido: debe ser core/form.html
    form_class = MenuItemForm
    success_message = "Ítem de menú creado con éxito"

    def get_success_url(self):
        if self.request.headers.get('Accept') == 'application/json/html':
            return JsonResponse({'success': True, 'message': self.success_message})
        else:
            return reverse_lazy('configuracion:menuitemlist')  # Corregido: debe ser configuracion:menuitemlist
    
    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        # La auditoría de creación se realizará automáticamente mediante las señales
        # No es necesario registrarla manualmente aquí
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Menu Item'
        context['entity'] = 'configuracion'  # Corregido: debe ser configuracion
        context['action'] = 'add'
        return context

class MenuItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'base.change_menuitem'  # Corregido: debe ser base.change_menuitem
    model = MenuItem
    template_name = 'core/form.html'  # Corregido: debe ser core/form.html
    form_class = MenuItemForm
    success_message = "Ítem de menú actualizado con éxito"

    def get_success_url(self):
        if self.request.headers.get('Accept') == 'application/json/html':
            return JsonResponse({'success': True, 'message': self.success_message})
        else:
            return reverse_lazy('configuracion:menuitemlist')  # Corregido: debe ser configuracion:menuitemlist
    
    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        # La auditoría de actualización se realizará automáticamente mediante las señales
        # No es necesario registrarla manualmente aquí
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Menu Item'
        context['entity'] = 'configuracion'  # Corregido: debe ser configuracion
        context['action'] = 'edit'
        return context