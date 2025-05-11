from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.translation import gettext as _

from apps.base.views.genericlistview import OptimizedSecureListView
from apps.notifications.backend.sms_backend import send_test_sms
from apps.notifications.forms.configure import SMSConfigurationForm
from apps.notifications.models.emailmodel import SMSConfiguration

# from .models import SMSConfiguration
# from .forms import SMSConfigurationForm
# from .utils import send_test_sms

# Vista de listado actualizada
class SMSConfigurationListView(OptimizedSecureListView):
    """
    Vista optimizada para listar configuraciones de SMS con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'sms.view_smsconfiguration'
    model = SMSConfiguration
    template_name = 'core/list.html'
    context_object_name = 'configurations'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['name', 'phone_number', 'backend', 'region']
    
    # Ordenamiento por defecto
    order_by = ('name',)
    
    # Atributos específicos
    title = _('Listado de Configuraciones de SMS')
    entity = _('Configuración de SMS')
    
    def get_queryset(self):
        # Usar select_related para optimizar las consultas si hay relaciones
        queryset = super().get_queryset()
        
        # Filtrado por estado (si aplica)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(is_active=(status == 'active'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['NOMBRE', 'BACKEND', 'NÚMERO', 'ESTADO']
        
        # Definir campos y cómo deben ser mostrados
        context['fields'] = ['name', 'backend', 'phone_number', 'status']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': _('Nueva Configuración'),
                'icon': 'add',
                'url': 'notificaciones:sms_config_create',
                'modal': False,
            }
        ]
        
        # Configuración de acciones
        context['actions'] = [
            {
                'name': 'edit',
                'icon': 'edit',
                'label': '',
                'color': 'primary',
                'color2': 'white',
                'url': 'notificaciones:sms_config_update',
                'modal': False
            },
            {
                'name': 'delete',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'url': 'notificaciones:sms_config_delete',
                'modal': True
            }
        ]
        
        # Agregar filtros para la vista
        context['status_choices'] = {
            'active': _('Activo'),
            'inactive': _('Inactivo')
        }
        
        # Configuración de toggle para activar/desactivar
        context['use_toggle'] = True
        context['toggle_field'] = 'is_active'
        context['toggle_url'] = 'notificaciones:smsconfiguration_toggle'
        
        return context
    
    def get_formatted_data(self, obj):
        """
        Personaliza el formato de los datos para la tabla.
        """
        data = super().get_formatted_data(obj)
        
        # Formatear estado
        status_classes = {
            True: 'bg-success text-white',
            False: 'bg-danger text-white',
        }
        status_texts = {
            True: _('Activo'),
            False: _('Inactivo'),
        }
        
        data['status'] = f'<span class="badge {status_classes.get(obj.is_active, "")}">'\
                        f'{status_texts.get(obj.is_active, "")}</span>'
        
        # Mostrar backend de forma más amigable
        if hasattr(obj, 'backend'):
            data['backend'] = obj.get_backend_display()
        
        # Si hay valores que necesitan formato especial
        if hasattr(obj, 'region'):
            data['region'] = f"{obj.region}" if obj.region else "—"
        
        # Formatear número de teléfono
        if hasattr(obj, 'phone_number'):
            data['phone_number'] = f"{obj.phone_number}" if obj.phone_number else "—"
        
        return data

class SMSConfigurationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SMSConfiguration
    form_class = SMSConfigurationForm
    # template_name = 'sms/configuration_form.html'
    template_name = 'notifications/config/sms_config.html'
    success_url = reverse_lazy('notificaciones:configuration_list')
    permission_required = 'sms.add_smsconfiguration'
    
    def form_valid(self, form):
        messages.success(self.request, 'Configuración SMS creada correctamente.')
        return super().form_valid(form)

class SMSConfigurationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SMSConfiguration
    form_class = SMSConfigurationForm
    template_name = 'sms/configuration_form.html'
    success_url = reverse_lazy('notificaciones:configuration_list')
    permission_required = 'sms.change_smsconfiguration'
    
    def form_valid(self, form):
        messages.success(self.request, 'Configuración SMS actualizada correctamente.')
        return super().form_valid(form)
    
# Vista de eliminación actualizada
class SMSConfigurationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SMSConfiguration
    template_name = 'core/del.html'  # Usar la misma plantilla genérica
    context_object_name = 'sms_config'
    permission_required = 'sms.delete_smsconfiguration'
    success_url = reverse_lazy('notificaciones:configuration_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Configuración de SMS')
        context['entity'] = _('Configuraciones de SMS')
        context['texto'] = _('¿Está seguro de eliminar la configuración "{}"?').format(self.object.name)
        context['list_url'] = 'notificaciones:configuration_list'
        return context
    
    def delete(self, request, *args, **kwargs):
        config = self.get_object()
        success_message = _('Configuración de SMS "{}" eliminada exitosamente').format(config.name)
        
        # Guardar el nombre antes de eliminar
        config_name = config.name
        
        # Realizar la eliminación
        self.object = config
        config.delete()
        
        # Respuesta mejorada para AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Configuración de SMS "{}" eliminada exitosamente').format(config_name),
                'redirect': str(self.success_url)
            })
        
        # Para solicitudes no-AJAX
        messages.success(request, success_message)
        return HttpResponseRedirect(self.get_success_url())
    
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


@login_required
@permission_required('sms.change_smsconfiguration')
@require_POST
def send_test_sms_view(request, pk):
    configuration = get_object_or_404(SMSConfiguration, pk=pk)
    phone_number = request.POST.get('test_phone_number')
    message = request.POST.get('test_message', 'Este es un mensaje SMS de prueba')
    
    try:
        result = send_test_sms(configuration, phone_number, message)
        if result['success']:
            messages.success(request, f'SMS de prueba enviado correctamente. ID del mensaje: {result["message_id"]}')
        else:
            messages.error(request, f'Error al enviar SMS de prueba: {result["error"]}')
    except Exception as e:
        messages.error(request, f'Error al enviar SMS de prueba: {str(e)}')
    
    return redirect('notificaciones:sms_config_update', pk=pk)