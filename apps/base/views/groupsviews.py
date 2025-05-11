from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect

from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from collections import defaultdict

from apps.base.forms.groupForm import GroupFormCreate

from apps.base.mixins.groupmixin import GroupViewMixin
from apps.base.views.genericlistview import OptimizedSecureListView

class GroupListView(OptimizedSecureListView):
    """
    Vista optimizada para listar grupos con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'auth.view_group'
    model = Group
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['name']
    # Ordenamiento por defecto
    order_by = ('name',)
    
    # Atributos específicos
    title = _('Listado de Grupos')
    entity = 'Grupos'
    
    def get_queryset(self):
        queryset = super().get_queryset()
       
        permission_id = self.request.GET.get('permission', '')
        if permission_id:
            queryset = queryset.filter(permissions__id=permission_id).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['GRUPO']
        context['fields'] = ['name']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': 'Crear Grupo',
                'icon': 'add',
                'url': 'configuracion:group_create',
            }
        ]
        
        # URL para exportar grupos si se desea implementar
        # context['url_export'] = 'configuracion:group-download'
        
        context['actions'] = [
            {
                'name': 'edit',
                'label': '',
                'icon': 'edit',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'configuracion:group_update',
            },
            {
                'name': 'delete',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'url': 'configuracion:group_delete',
                'modal': True
            }
        ]
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('configuracion:group_list')
        
        return context
    
class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, GroupViewMixin, CreateView):
    permission_required = 'auth.add_group'
    model = Group
    template_name = 'groups/groups.html'
    fields = ['name']
    success_url = reverse_lazy('configuracion:groups_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Grupo')
        context['entity'] = _('Grupos')
        context['list_url'] = 'configuracion:groups_list'
        context['action'] = 'add'
        
        # Obtener todos los permisos
        all_permissions = self.get_all_permissions()
        
        # Pasar al contexto
        context['all_permissions'] = all_permissions
        context['selected_permissions'] = Permission.objects.none()  # Vacío para crear
        
        return context

    def form_valid(self, form):
        # Primero guardar el grupo para obtener su ID
        self.object = form.save()
        
        # Ahora actualizar los permisos
        if 'permissions_to' in self.request.POST:
            # Si estás usando el modo de selección dual (from/to)
            permissions_ids = self.request.POST.getlist('permissions_to')
        else:
            # Si estás usando checkboxes directos
            permissions_ids = self.request.POST.getlist('permissions')
            
        if permissions_ids:
            permissions = Permission.objects.filter(id__in=permissions_ids)
            # Usar el método set() en lugar de add() para la relación many-to-many
            self.object.permissions.set(permissions)
            # Guardar el grupo después de asignar permisos
            self.object.save()
        
        messages.success(self.request, _('Grupo creado exitosamente'))
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, _('Por favor corrija los errores en el formulario'))
        return super().form_invalid(form)

    
class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Group
    template_name = 'groups/groups.html'
    fields = ['name']
    permission_required = 'auth.change_group'
    success_url = reverse_lazy('configuracion:groups_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Actualizar Grupo')
        context['entity'] = _('Grupos')
        context['list_url'] = 'configuracion:groups_list'
        context['action'] = 'update'
        
        # Obtener los permisos actuales para poblar el selector de permisos
        perm_queryset = Permission.objects.all().select_related('content_type')
        
        # Añadir al contexto para que esté disponible en el template
        context['all_permissions'] = perm_queryset
        context['selected_permissions'] = self.object.permissions.all()
        
        return context
    
    def form_valid(self, form):
        # Primero guardar los cambios en el nombre del grupo
        response = super().form_valid(form)
        
        # Ahora actualizar los permisos
        if 'permissions_to' in self.request.POST:
            # Si estás usando el modo de selección dual (from/to)
            permissions_ids = self.request.POST.getlist('permissions_to')
        else:
            # Si estás usando checkboxes directos
            permissions_ids = self.request.POST.getlist('permissions')
            
        if permissions_ids:
            permissions = Permission.objects.filter(id__in=permissions_ids)
            self.object.permissions.set(permissions)
        else:
            # Si no hay permisos seleccionados, eliminar todos
            self.object.permissions.clear()
        
        messages.success(self.request, _('Grupo actualizado exitosamente'))
        return response


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Group
    template_name = 'core/del.html'
    context_object_name = 'group'
    permission_required = 'auth.delete_group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Grupo'
        context['entity'] = 'Grupos'
        context['texto'] = f'Seguro de eliminar el Grupo {self.object}?'
        context['list_url'] = 'configuracion:groups_list'
        return context
    
    def delete(self, request, *args, **kwargs):
        group = self.get_object()
        success_message = _(f'Grupo "{group.name}" eliminado exitosamente')
        
        # Guardar el nombre antes de eliminar
        group_name = group.name
        
        # Realizar la eliminación
        self.object = group
        group.delete()
        
        # Respuesta mejorada para AJAX - usar mayúsculas en X-Requested-With
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Obtenemos la URL de éxito sin usar resolve()
            success_url = reverse_lazy('configuracion:groups_list')
            return JsonResponse({
                'success': True,
                'message': _(f'Grupo "{group_name}" eliminado exitosamente'),
                'redirect': str(success_url)
            })
        
        # Para solicitudes no-AJAX
        messages.success(request, success_message)
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('configuracion:groups_list')
    
    def post(self, request, *args, **kwargs):
        # Verificar si es una petición AJAX para confirmar eliminación
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                return self.delete(request, *args, **kwargs)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=500)
        return super().post(request, *args, **kwargs)