from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

# Importamos el modelo AuditLog para registrar acciones específicas
from apps.audit.models import AuditLog
from apps.base.forms.menuform import MenuForm, MenuItemForm
from apps.base.models.menu import Menu, MenuItem

class ToggleMenuEstadoView(LoginRequiredMixin, UpdateView):
    model = Menu
    fields = ['is_active']
    success_url = reverse_lazy('configuracion:menu')

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        menu = get_object_or_404(Menu, pk=kwargs['pk'])
        
        # Guardamos el estado anterior para la auditoría
        estado_anterior = menu.is_active
        
        # Invertir el estado
        menu.is_active = not menu.is_active
        menu.save()
        
        # Registrar manualmente en la auditoría
        AuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            content_type=ContentType.objects.get_for_model(Menu),
            object_id=str(menu.pk),
            table_name=Menu._meta.db_table,
            data_before={'is_active': estado_anterior},
            data_after={'is_active': menu.is_active},
            description=f"Cambio de estado del menú '{menu.name}' de {'activo' if estado_anterior else 'inactivo'} a {'activo' if menu.is_active else 'inactivo'}"
        )
        
        return JsonResponse({
            'success': True, 
            'is_active': menu.is_active,
            'message': f"Menú {menu.name} {'activado' if menu.is_active else 'desactivado'} correctamente"
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Activar/Desactivar Menú'
        context['entity'] = 'Menú'
        context['list_url'] = 'configuracion:menu'
        return context

class ToggleMenuItelEstadoView(LoginRequiredMixin, UpdateView):
    model = MenuItem
    fields = ['is_active']
    success_url = reverse_lazy('configuracion:menuitemlist')

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        menu_item = get_object_or_404(MenuItem, pk=kwargs['pk'])
        
        # Guardamos el estado anterior para la auditoría
        estado_anterior = menu_item.is_active
        
        # Invertir el estado
        menu_item.is_active = not menu_item.is_active
        menu_item.save()
        
        # Registrar manualmente en la auditoría
        AuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            content_type=ContentType.objects.get_for_model(MenuItem),
            object_id=str(menu_item.pk),
            table_name=MenuItem._meta.db_table,
            data_before={'is_active': estado_anterior},
            data_after={'is_active': menu_item.is_active},
            description=f"Cambio de estado del ítem de menú '{menu_item.name}' de {'activo' if estado_anterior else 'inactivo'} a {'activo' if menu_item.is_active else 'inactivo'}"
        )
        
        return JsonResponse({
            'success': True, 
            'is_active': menu_item.is_active,
            'message': f"Ítem de menú {menu_item.name} {'activado' if menu_item.is_active else 'desactivado'} correctamente"
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Activar/Desactivar Ítem de Menú'
        context['entity'] = 'Ítem de Menú'
        context['list_url'] = 'configuracion:menuitemlist'
        return context

class ListMenuView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'configuracion.view_menu'
    model = Menu
    template_name = 'core/list.html'  # Esta debe ser la ruta correcta a tu plantilla
    
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
        context['title'] = 'Menu'
        context['entity'] = 'configuracion'
        context['headers'] = ['NOMBRE', 'ICONO', 'ACTIVO']
        context['fields'] = ['name', 'icon']
        context['url_toggle'] = 'configuracion:togglemenu'  # Ajustado al nuevo namespace
        context['actions'] = [
            {
                'name': 'edit',
                'icon': 'edit',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'configuracion:menu_edit',  # Ajustado al nuevo namespace
                'modal': 'Activar'
            }
        ]
        context['cancel_url'] = reverse_lazy('configuracion:menu')  # Correcto si este es el nuevo namespace
        return context

class MenuCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'base.add_menu'
    model = Menu
    template_name = 'core/form.html'
    form_class = MenuForm  # Corregido: Debe ser MenuForm, no MenuItem
    success_url = reverse_lazy('configuration:menu')
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
        context['entity'] = 'configuration'
        context['action'] = 'add'
        return context

class MenuUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'configuration.change_menu'
    model = Menu
    template_name = 'configuration/create.html'
    form_class = MenuForm
    success_message = "Menú actualizado con éxito"
        
    def get_success_url(self):
        if self.request.accepts('application/json/html'):
            return JsonResponse({'success': True, 'message': self.success_message})
        else:
            return reverse_lazy('configuration:menu')
        
    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        # La auditoría de actualización se realizará automáticamente mediante las señales
        # No es necesario registrarla manualmente aquí
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Menu'
        context['entity'] = 'configuration'
        context['action'] = 'edit'
        return context

class MenuItemListView(ListView):
    model = MenuItem
    template_name = 'core/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Menu'
        context['entity'] = 'configuracion'
        context['headers'] = ['MENU', 'NOMBRE', 'URL', 'ICONO', 'ACTIVO']
        context['fields'] = ['menu', 'name', 'url_name', 'icon']
        context['url_toggle'] = 'configuracion:togglemenuitem'
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': 'Agregar',
                'icon': 'add',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'configuracion:menuitem_create',
                'modal': 'Activar'
            }
        ]
        
        context['actions'] = [
            {
                'name': 'edit',
                'icon': 'edit',                
                'color': 'secondary',
                'color2': 'brown',
                'url': 'configuracion:menuitem_edit',
                'modal': 'Activar'
            }
            ]
        context['cancel_url'] = reverse_lazy('configuracion:menu')
        
        return context

# class MenuItemListView(LoginRequiredMixin, ListView):
#     model = MenuItem
#     template_name = 'core/list.html'

#     def get_queryset(self):
#         queryset = super().get_queryset()
        
#         # Registrar la acción de visualización de lista en la auditoría
#         AuditLog.objects.create(
#             user=self.request.user,
#             action='VIEW',
#             content_type=ContentType.objects.get_for_model(MenuItem),
#             table_name=MenuItem._meta.db_table,
#             description=f"Visualización de lista de ítems de menú"
#         )
        
#         return queryset

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = 'Menu'
#         context['entity'] = 'configuration'
#         context['headers'] = ['MENU', 'NOMBRE', 'URL', 'ICONO', 'ACTIVO']
#         context['fields'] = ['menu', 'name', 'url_name', 'icon']
#         context['url_toggle'] = 'configuracion:togglemenuitem'
#         context['Btn_Add'] = [
#             {
#                 'name': 'add',
#                 'label': 'Agregar',
#                 'icon': '',
#                 'color': 'secondary',
#                 'color2': 'brown',
#                 'url': 'configuration:menuitem_create',
#                 'modal': 'Activar'
#             }
#         ]
        
#         context['actions'] = [
#             {
#                 'name': 'edit',
#                 'icon': 'edit',                
#                 'color': 'secondary',
#                 'color2': 'brown',
#                 'url': 'configuration:menuitem_edit',
#                 'modal': 'Activar'
#             }
#         ]
#         context['cancel_url'] = reverse_lazy('configuration:menu')
        
#         return context

class MenuItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'base.add_menu'
    model = MenuItem
    template_name = 'core/create.html'
    form_class = MenuItemForm
    success_message = "Ítem de menú creado con éxito"

    def get_success_url(self):
        if self.request.accepts('application/json/html'):
            return JsonResponse({'success': True, 'message': self.success_message})
        else:
            return reverse_lazy('configuration:menuitemlist')
    
    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        # La auditoría de creación se realizará automáticamente mediante las señales
        # No es necesario registrarla manualmente aquí
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Menu Item'
        context['entity'] = 'configuration'
        context['action'] = 'add'
        return context

class MenuItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'configuration.change_menuitem'
    model = MenuItem
    template_name = 'configuration/create.html'
    form_class = MenuItemForm
    success_message = "Ítem de menú actualizado con éxito"

    def get_success_url(self):
        if self.request.accepts('application/json/html'):
            return JsonResponse({'success': True, 'message': self.success_message})
        else:
            return reverse_lazy('configuration:menuitemlist')
    
    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        # La auditoría de actualización se realizará automáticamente mediante las señales
        # No es necesario registrarla manualmente aquí
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Menu Item'
        context['entity'] = 'configuration'
        context['action'] = 'edit'
        return context