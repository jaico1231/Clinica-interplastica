# notifications/views.py

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin # Opcional: para permisos
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages # Para feedback al usuario
from django.utils.translation import gettext_lazy as _
from apps.base.views.genericlistview import OptimizedSecureListView
from apps.notifications.models.emailmodel import EmailConfiguration, SMSConfiguration, WhatsAppConfiguration
from apps.notifications.forms.configure import EmailConfigurationForm, SMSConfigurationForm, WhatsAppConfigurationForm

# Mixin común para URLs de éxito y mensajes
class SuccessMessageMixin:
    success_message = "Configuration saved successfully."

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

# --- Email Configuration Views ---

class EmailConfigurationListView(OptimizedSecureListView):
    """
    Vista optimizada para listar configuraciones de email con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'emails.view_emailconfiguration'
    model = EmailConfiguration
    template_name = 'core/list.html'
    context_object_name = 'configurations'
    
    # Definir explícitamente los campos para búsqueda correctos
    search_fields = ['name', 'from_email', 'host', 'description']
    
    # Ordenamiento por defecto
    order_by = ('name',)
    
    # Atributos específicos
    title = _('Listado de Configuraciones de Email')
    entity = _('Configuración de Email')
    
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
        context['headers'] = ['NOMBRE', 'EMAIL', 'HOST', 'PUERTO']
        
        # Definir campos y cómo deben ser mostrados
        context['fields'] = ['name', 'from_email', 'host', 'port']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': _('Nueva Configuración'),
                'icon': 'add',
                'url': 'notificaciones:email_config_create',
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
                'url': 'notificaciones:email_config_update',
                'modal': False
            },
            {
                'name': 'delete',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'url': 'notificaciones:email_config_delete',
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
        context['toggle_url'] = 'notificaciones:emailconfiguration_toggle'
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('dashboard')
        
        # Agregar estadísticas
        current_configurations = self.get_queryset()
        context['stats'] = {
            'total_count': current_configurations.count(),
            'active_count': current_configurations.filter(is_active=True).count(),
            'inactive_count': current_configurations.filter(is_active=False).count(),
        }
        
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
        
        # Si hay valores que necesitan formato especial
        if hasattr(obj, 'port'):
            data['port'] = f"{obj.port}" if obj.port else "—"
        
        # Truncar descripción si es muy larga
        if hasattr(obj, 'description') and obj.description:
            if len(obj.description) > 50:
                data['description'] = f"{obj.description[:50]}..."
        
        return data

class EmailConfigMixin:
    """Mixin común para las vistas de configuración de email"""
    model = EmailConfiguration
    form_class = EmailConfigurationForm
    template_name = 'notifications/config/email_config.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_verbose_name'] = self.model._meta.verbose_name
        return context

class EmailConfigurationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'notifications.add_emailconfiguration'
    model = EmailConfiguration
    form_class = EmailConfigurationForm
    template_name = 'notifications/config/email_config.html'
    # template_name = 'core/form.html'  # Usar la plantilla genérica de formularios
    success_message = _('Configuración de email creada exitosamente')  # Mensaje movido aquí

    def get_success_url(self):
        return reverse_lazy('notificaciones:email_config_list')

    def form_valid(self, form):
        # --- Guardar y mostrar datos de la instancia ---
        response = super().form_valid(form)
        print("\n--- Instancia guardada ---")
        print("ID:", self.object.id)
        print("Nombre:", self.object.name)
        print("Backend:", self.object.backend)
        print("Host:", self.object.host)
        print("API Key:", bool(self.object.api_key))  # No imprimir el valor real por seguridad
        print("Password:", bool(self.object.password))
        
        return response

    def form_invalid(self, form):
        print("\n--- Formulario inválido ---")
        print("Errores:", form.errors)
        print("Datos enviados:", form.data)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Nueva Configuración de Email')
        context['entity'] = _('Configuración de Email')
        context['list_url'] = reverse_lazy('notificaciones:email_config_list')
        return context

class EmailConfigurationUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = 'notifications.change_emailconfiguration'
    model = EmailConfiguration
    form_class = EmailConfigurationForm
    template_name = 'notifications/config/email_config.html'
    # template_name = 'core/form.html'  # Usar la plantilla genérica de formularios

    def get_success_url(self):
        return reverse_lazy('notificaciones:email_config_list')
    
    def form_valid(self, form):
        # --- Depuración: Imprimir datos recibidos ---
        print("\n--- Datos del formulario ---")
        print("Datos limpios:", form.cleaned_data)
        print("Errores:", form.errors)
        
        # --- Si hay errores, mostrar form_invalid ---
        if form.errors:
            print("Errores detectados. No se procede a guardar.")
            return self.form_invalid(form)
        
        # --- Guardar y mostrar datos de la instancia ---
        response = super().form_valid(form)
        print("\n--- Instancia guardada ---")
        print("ID:", self.object.id,"\n")
        print("Nombre:", self.object.name)
        print("Backend:", self.object.backend)
        print("Host:", self.object.host)
        print("API Key:", bool(self.object.api_key))  # No imprimir el valor real por seguridad
        print("Password:", bool(self.object.password))
        
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Actualizar Configuración de Email')
        context['entity'] = _('Configuración de Email')
        context['list_url'] = reverse_lazy('notificaciones:email_config_list')
        return context

class EmailConfigurationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = EmailConfiguration
    template_name = 'core/del.html'  # Usar la misma plantilla genérica que GroupDeleteView
    context_object_name = 'email_config'
    permission_required = 'notifications.delete_emailconfiguration'
    success_url = reverse_lazy('notificaciones:email_config_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Configuración de Email'
        context['entity'] = 'Configuraciones de Email'
        context['texto'] = f'¿Está seguro de eliminar la configuración "{self.object.name}"?'
        context['list_url'] = 'notificaciones:email_config_list'
        return context
    
    def delete(self, request, *args, **kwargs):
        config = self.get_object()
        success_message = _(f'Configuración de email "{config.name}" eliminada exitosamente')
        
        # Guardar el nombre antes de eliminar
        config_name = config.name
        
        # Realizar la eliminación
        self.object = config
        config.delete()
        
        # Respuesta mejorada para AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _(f'Configuración de email "{config_name}" eliminada exitosamente'),
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

