from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.db.models import Q
from django.db.models.functions import Concat
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, FormView, TemplateView
from apps.base.models.users import User
from django.utils.translation import gettext_lazy as _
from apps.base.forms.userform import PasswordChangeForm, UserForm
from apps.audit.signals import AuditableModelMixin
import logging

from apps.base.views.genericlistview import OptimizedSecureListView

logger = logging.getLogger(__name__)

class UserListView(OptimizedSecureListView):
    """
    Vista optimizada para listar usuarios con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'base.view_user'
    model = User
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['username', 'first_name', 'last_name', 'email', 'NumeroIdentificacion']
    # Ordenamiento por defecto
    order_by = ('username', 'last_name')
    
    # Atributos específicos
    title = 'Listado de usuarios'
    entity = 'Usuario'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Búsqueda personalizada para "sin email", "sin nombre", etc.
        missing_field = self.request.GET.get('missing', '')
        if missing_field:
            if missing_field == 'email':
                queryset = queryset.filter(Q(email__isnull=True) | Q(email=''))
            elif missing_field == 'first_name':
                queryset = queryset.filter(Q(first_name__isnull=True) | Q(first_name=''))
            elif missing_field == 'last_name':
                queryset = queryset.filter(Q(last_name__isnull=True) | Q(last_name=''))
        
        # Usuarios inactivos por más de 6 meses
        if self.request.GET.get('inactive') == 'true':
            six_months_ago = timezone.now() - timezone.timedelta(days=180)
            queryset = queryset.filter(
                Q(last_login__lt=six_months_ago) | Q(last_login__isnull=True)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['NOMBRE DE USUARIO', 'NOMBRE', 'APELLIDO', 'CORREO', 'CEDULA']
        context['fields'] = ['username', 'first_name', 'last_name', 'email', 'NumeroIdentificacion']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': 'Crear usuario',
                'icon': 'add',
                'url': 'configuracion:user_create',
                'modal': True,
            }
        ]
        
        # URL para exportar usuarios
        
        context['actions'] = [
            {
                'name': 'edit',
                'label': '',
                'icon': 'edit',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'configuracion:user_edit',
                'modal': True
            },
            {
                'name': 'delete',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'url': 'configuracion:user_delete',
                'modal': True
            },
            {
                'name': 'password',
                'label': '',
                'icon': 'lock',
                'color': 'link',
                'color2': 'green',
                'url': 'configuracion:change_password',
                'modal': True
            }
        ]
        
        # Configuración para toggle
        if hasattr(self.model, 'is_active'):
            context['use_toggle'] = True
            context['url_toggle'] = 'configuracion:toggle_active_status'
            # Pasar información adicional para la URL genérica
            context['toggle_app_name'] = self.model._meta.app_label
            context['toggle_model_name'] = self.model._meta.model_name
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('configuracion:users_list')
        
        return context

class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear usuarios
    La auditoría es manejada automáticamente por las señales post_save
    """
    permission_required = 'base.add_user'
    model = User
    form_class = UserForm
    template_name = 'core/create.html'
    
    def get_success_url(self):
        return reverse_lazy('configuracion:users_list')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        # Guardar relaciones M2M si existen
        form.save_m2m()
        
        messages.success(self.request, _('Usuario creado con éxito'))
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Usuario creado con éxito'),
                'redirect': reverse_lazy('configuracion:users_list').resolve(self.request)
            })
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
                
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
            
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Usuario')
        context['entity'] = _('Usuario')
        context['list_url'] = reverse_lazy('configuracion:users_list')
        context['action'] = 'add'
        return context

class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para actualizar usuarios
    La auditoría es manejada automáticamente por las señales pre_save y post_save
    """
    permission_required = 'base.change_user'
    model = User
    form_class = UserForm
    template_name = 'core/create.html'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Hacer el campo de contraseña opcional para actualizaciones
        if 'password' in form.fields:
            form.fields['password'].required = False
        return form
    
    def get_success_url(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Para respuestas AJAX (modals)
            return None
        return reverse_lazy('configuracion:users_list')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        
        # Actualizar contraseña solo si se proporciona una nueva
        password = form.cleaned_data.get('password')
        if password:
            user.set_password(password)
            
        user.save()
        
        # Guardar relaciones M2M si existen
        form.save_m2m()
        
        messages.success(self.request, _('Usuario actualizado con éxito'))
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Usuario actualizado con éxito'),
                'redirect': reverse('configuracion:users_list')
            })
            
        return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
                
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
            
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Usuario')
        context['entity'] = _('Usuario')
        context['list_url'] = reverse_lazy('configuracion:users_list')
        context['action'] = 'edit'
        return context

    
class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Vista para eliminar usuarios
    La auditoría es manejada automáticamente por la señal post_delete
    """
    permission_required = 'base.delete_user'
    model = User
    template_name = 'core/del.html'
    success_url = reverse_lazy('configuracion:users_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Usuario')
        context['entity'] = _('Usuario')
        context['list_url'] = reverse_lazy('configuracion:users_list')
        return context
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Validaciones de eliminación
        if user == request.user:
            messages.error(request, _("No puedes eliminarte a ti mismo."))
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': _("No puedes eliminarte a ti mismo.")
                }, status=400)
                
            return redirect(self.success_url)
            
        # Evitar eliminar al superadmin
        if user.is_superuser and user.username == 'admin':
            messages.error(request, _("No se puede eliminar al usuario administrador principal."))
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': _("No se puede eliminar al usuario administrador principal.")
                }, status=400)
                
            return redirect(self.success_url)
        
        # Eliminar el usuario - la auditoría se maneja por la señal post_delete
        response = super().delete(request, *args, **kwargs)
        
        messages.success(request, _("Usuario eliminado con éxito."))
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _("Usuario eliminado con éxito."),
                'redirect': self.success_url
            })
            
        return response


class ChangePasswordView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista para cambiar la contraseña de un usuario
    No requiere configuración especial para auditoría, ya que user.save()True las señales
    """
    permission_required = 'base.change_user'
    
    def get(self, request, pk):
        # Para solicitudes AJAX que cargan el formulario en un modal
        user = get_object_or_404(User, pk=pk)
        context = {
            'user': user,
            'form_action': reverse_lazy('base:change_password', kwargs={'pk': pk})
        }
        # Aquí podrías renderizar una plantilla parcial para el modal
        # O simplemente retornar un error si no es soportado
        return JsonResponse({'success': False, 'message': _('Método no soportado')})
    
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = PasswordChangeForm(request.POST)
        
        if form.is_valid():
            # Cambiar contraseña - la auditoría registrará el cambio cuando se llame a save()
            password = form.cleaned_data.get('password1')
            user.set_password(password)
            user.save()
            
            messages.success(request, _("Contraseña cambiada exitosamente."))
            return JsonResponse({'success': True, 'message': _("Contraseña cambiada exitosamente.")})
        else:
            # Procesar errores del formulario
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
                
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)


class ToggleUserStatusView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista paraTruedeTrueusuarios
    La auditoría se maneja con las señales de pre_save y post_save cuando se llama a user.save()
    """
    permission_required = 'base.change_user'
    
    def post(self, request, pk):
        try:
            user = get_object_or_404(User, pk=pk)
            
            # Validaciones
            if user.is_superuser and user.username == 'admin':
                return JsonResponse({
                    'success': False,
                    'message': _('No se puede deTrueal administrador principal')
                }, status=400)
                
            if user == request.user:
                return JsonResponse({
                    'success': False,
                    'message': _('No puedes deTruee a ti mismo')
                }, status=400)
            
            # Cambiar estado - la auditoría registrará el cambio automáticamente 
            user.is_active = not user.is_active
            user.save()
            
            status_msg = _("activado") if user.is_active else _("desactivado")
            
            return JsonResponse({
                'success': True,
                'is_active': user.is_active,
                'message': _("Usuario {} {} correctamente").format(user.username, status_msg)
            })
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _("Usuario no encontrado")
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': _("Error: {}").format(str(e))
            }, status=500)