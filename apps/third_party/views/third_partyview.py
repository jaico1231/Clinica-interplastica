from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.base.views.genericlistview import OptimizedSecureListView
from apps.third_party.forms.third_partyform import ThirdPartyForm
from apps.third_party.models.third_party import ThirdParty
from apps.base.views.genericcsvimportview import GenericCSVImportView
from apps.base.views.genericexportview import GenericExportView



class ThirdPartyListView(OptimizedSecureListView):
    """
    Vista optimizada para listar terceros con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'third_party.view_thirdparty'
    model = ThirdParty
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['first_name', 'last_name', 'document_number', 'email', 'mobile']
    # Ordenamiento por defecto
    order_by = ('last_name', 'first_name')
    
    # Atributos específicos
    title = _('Listado de Terceros')
    entity = _('Tercero')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Búsqueda personalizada para "sin email", "sin teléfono", etc.
        missing_field = self.request.GET.get('missing', '')
        if missing_field:
            if missing_field == 'email':
                queryset = queryset.filter(Q(email__isnull=True) | Q(email=''))
            elif missing_field == 'phone':
                queryset = queryset.filter(Q(mobile__isnull=True) | Q(mobile=''))
            elif missing_field == 'address':
                queryset = queryset.filter(Q(address__isnull=True) | Q(address=''))
        
        # Terceros inactivos por más de 6 meses
        if self.request.GET.get('inactive') == 'true':
            six_months_ago = timezone.now() - timezone.timedelta(days=180)
            # Ajusta según tu modelo específico
            if hasattr(self.model, 'last_login'):
                queryset = queryset.filter(
                    Q(last_login__lt=six_months_ago) | Q(last_login__isnull=True)
                )
            elif hasattr(self.model, 'last_activity'):
                queryset = queryset.filter(
                    Q(last_activity__lt=six_months_ago) | Q(last_activity__isnull=True)
                )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['NOMBRE', 'APELLIDO', 'DOCUMENTO', 'TELEFONO_FIJO', 'CELULAR', 'EMAIL']
        context['fields'] = ['first_name', 'last_name', 'document_number', 'landline', 'mobile', 'email']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': _('Crear Tercero'),
                'icon': 'add',
                'url': 'administracion terceros:third-party_create',
                'modal': True,
            },
            {
                'name': 'import',
                'label': _('Importar CSV'),
                'icon': 'file_upload',
                'url': 'administracion terceros:third-party-upload',
                'modal': False,
            }
        ]
        
        context['url_export'] = 'administracion terceros:third-party-download'
        
        context['actions'] = [
            {
                'name': 'edit',
                'label': '',
                'icon': 'edit',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'administracion terceros:third-party_update',
                'modal': True
            },
            {
                'name': 'del',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'url': 'administracion terceros:third-party_delete',
                'modal': True
            }
        ]
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('administracion terceros:third-party_list')
        
        return context

class ThirdPartyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear un nuevo tercero
    La auditoría se maneja automáticamente por las señales post_save
    """
    permission_required = 'third_party.add_thirdparty'
    model = ThirdParty
    form_class = ThirdPartyForm
    template_name = 'core/create.html'
    
    def get_success_url(self):
        return reverse_lazy('administracion terceros:third-party-list')
    
    def form_valid(self, form):
        # Guardar el tercero - la auditoría se maneja por señales
        self.object = form.save()
        
        messages.success(self.request, _('Tercero creado con éxito'))
        
        # Verificar si es una solicitud AJAX
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Tercero creado con éxito'),
                'redirect': self.get_success_url().resolve(self.request)
            })
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        print('entraste en form invalid')
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
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
        context['title'] = _('Crear Tercero')
        context['entity'] = _('Tercero')
        context['list_url'] = reverse_lazy('administracion terceros:third-party-list')
        context['action'] = 'add'
        return context
    
class ThirdPartyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para actualizar información de un tercero
    La auditoría es manejada automáticamente por las señales pre_save y post_save
    """
    permission_required = 'third_party.change_thirdparty'
    model = ThirdParty
    form_class = ThirdPartyForm
    template_name = 'core/create.html'
    
    def get_success_url(self):
        return reverse_lazy('administracion terceros:third-party-list')
    
    def form_valid(self, form):
        # Guardar el tercero - la auditoría se maneja por señales
        self.object = form.save(commit=True)
        
        messages.success(self.request, _('Tercero actualizado con éxito'))
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Tercero actualizado con éxito'),
                'redirect': self.get_success_url().resolve(self.request)
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
        context['title'] = _('Editar Tercero')
        context['entity'] = _('Tercero')
        context['list_url'] = reverse_lazy('administracion terceros:third-party-list')
        context['action'] = 'edit'
        return context

class ThirdPartyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Vista para eliminar un tercero
    La auditoría es manejada automáticamente por la señal post_delete
    """
    permission_required = 'third_party.delete_thirdparty'
    model = ThirdParty
    template_name = 'core/del.html'
    context_object_name = 'Tercero'
    success_url = reverse_lazy('administracion terceros:third-party-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Tercero')
        context['entity'] = _('Tercero')
        context['texto'] = f'Seguro de eliminar el Tercero {self.object}?'
        context['list_url'] = reverse_lazy('administracion terceros:third-party-list')
        return context
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        try:
            # La auditoría se maneja automáticamente con la señal post_delete
            self.object.delete()
            messages.success(request, _('Tercero eliminado con éxito'))
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': _('Tercero eliminado con éxito'),
                    'redirect': self.success_url
                })
                
            return redirect(self.success_url)
            
        except Exception as e:
            # Capturar errores de integridad referencial
            error_message = _('No se puede eliminar el tercero porque está siendo utilizado en otros registros')
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=400)
                
            messages.error(request, error_message)
            return redirect(self.success_url)

class ToggleThirdPartyStatusView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para activar/desactivar terceros
    La auditoría se maneja con las señales de pre_save y post_save
    """
    permission_required = 'third_party.change_thirdparty'
    model = ThirdParty
    http_method_names = ['post']
    fields = ['status']
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Cambiar estado - la auditoría registrará el cambio automáticamente
        self.object.status = not self.object.status
        self.object.save(update_fields=['status'])
        
        status_msg = _("activado") if self.object.status else _("desactivado")
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'status': self.object.status,
                'message': _("Tercero {} correctamente").format(status_msg)
            })
            
        messages.success(request, _("Tercero {} correctamente").format(status_msg))
        return redirect('administracion terceros:third-party-list')

class ThirdPartyImportView(GenericCSVImportView):
    """
    Vista para importar terceros desde un archivo CSV
    """
    model = ThirdParty
    form_class = ThirdPartyForm
    success_url = reverse_lazy('administracion terceros:third-party-list')
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Importar Terceros')
        context['entity'] = _('Tercero')
        context['list_url'] = self.success_url
        return context
    
    def clean_row_data(self, row):
        """
        Sobrescribimos este método para manejar conversiones específicas
        para el modelo ThirdParty
        """
        cleaned_data = super().clean_row_data(row)
        
        # Manejo específico para campos del modelo ThirdParty
        # Por ejemplo, verificar que document_type e is_active estén correctos
        if 'document_type' in cleaned_data:
            # Normalizar tipo de documento (convertir a mayúsculas)
            cleaned_data['document_type'] = cleaned_data['document_type'].upper()
        
        return cleaned_data
    
class ThirdPartyExportView(GenericExportView):
    model = ThirdParty
    fields = ['first_name', 'last_name', 'document_number','landline','mobile','email','address','third_party_type']
    permission_required = 'third_party.view_thirdparty'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ... configuraciones existentes ...
        
        # Agregar formatos disponibles
        context['export_formats'] = [
            {'format': 'csv', 'label': 'CSV'},
            {'format': 'pdf', 'label': 'PDF'},
            {'format': 'excel', 'label': 'Excel'}
        ]
        
        return context