from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from apps.base.forms.companyform import CompanyAreaForm, CompanyForm
from apps.base.models.company import Company, CompanyArea
from apps.base.views.genericcsvimportview import GenericCSVImportView
from apps.base.views.genericexportview import GenericExportView
from apps.base.views.genericlistview import OptimizedSecureListView
from django.shortcuts import get_object_or_404
from django.db.models.deletion import ProtectedError
from apps.base.views.genericToggleIs_active import add_toggle_context
class CompanyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'base/company/company_form.html'
    success_url = reverse_lazy('company_list')
    permission_required = 'base.add_company'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Empresa')
        context['action'] = 'create'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Empresa creada exitosamente'))
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, _('Error al crear la empresa. Por favor, revise los datos ingresados.'))
        return super().form_invalid(form)

class CompanyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'company/company.html'
    context_object_name = 'company'
    permission_required = 'base.change_company'
    
    def get_object(self, queryset=None):
        """Override to always return the object with pk=1."""
        return self.model.objects.get(pk=1)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Actualizar Empresa')
        context['action'] = 'update'
        # Asegurarse de que la empresa con id=1 esté disponible
        context['company'] = self.get_object()
        return context
    
    def get_success_url(self):
        # Obtiene la URL anterior para redirigir después de la actualización
        referer = self.request.META.get('HTTP_REFERER')
        # Si no hay referer, redirige a la vista de detalle como fallback
        if not referer:
            return reverse_lazy('company_detail', kwargs={'pk': 1})
        return referer
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Empresa actualizada exitosamente'))
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, _('Error al actualizar la empresa. Por favor, revise los datos ingresados.'))
        return super().form_invalid(form)




# Primero, definamos el formulario para CompanyArea

# Ahora las vistas del CRUD
class CompanyAreaListView(OptimizedSecureListView):
    """
    Vista optimizada para listar áreas de la empresa con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'base.view_companyarea'
    model = CompanyArea
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['name', 'description', 'company__name']
    # Ordenamiento por defecto
    order_by = ('company__name', 'name')
    
    # Atributos específicos
    title = _('Listado de Áreas de la Empresa')
    entity = _('Área')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por compañía si se proporciona
        company_id = self.request.GET.get('company', '')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        
        # Filtrar por manager si se proporciona
        manager_id = self.request.GET.get('manager', '')
        if manager_id:
            queryset = queryset.filter(default_manager_id=manager_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['EMPRESA', 'NOMBRE', 'DESCRIPCIÓN', 'RESPONSABLE']
        context['fields'] = ['company__name', 'name', 'description', 'default_manager__username']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': _('Crear Área'),
                'icon': 'add',
                'url': 'configuracion:companyarea_create',
                'modal': True,
            }
        ]
        
        context['actions'] = [
            {
                'name': 'edit',
                'icon': 'edit',
                'label': '',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'configuracion:companyarea_update',
                'modal': True
            },
            {
                'name': 'delete',
                'icon': 'delete',
                'label': '',
                'color': 'danger',
                'color2': 'white',
                'url': 'configuracion:companyarea_delete',
                'modal': True
            }
        ]
        
        # Configuración para toggle si el modelo tiene is_active
        if hasattr(self.model, 'is_active'):
            context['use_toggle'] = True
            context['url_toggle'] = 'configuracion:toggle_active_status'
            context['toggle_app_name'] = self.model._meta.app_label
            context['toggle_model_name'] = self.model._meta.model_name
        
        # Obtener empresas para el filtro
        context['companies'] = Company.objects.filter(is_active=True)
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('configuracion:companyarea_list')
        
        return context


class CompanyAreaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'base.add_companyarea'
    model = CompanyArea
    template_name = 'core/create.html'
    form_class = CompanyAreaForm
    success_message = _("Área creada con éxito")
    
    def get_success_url(self):
        return reverse_lazy('configuracion:companyarea_list')
    
    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        
        # La auditoría de creación se realizará automáticamente mediante las señales
        
        response = super().form_valid(form)
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': self.success_message,
                'redirect': self.get_success_url().resolve(self.request)
            })
        
        return response
    
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
        context['title'] = _('Crear Área')
        context['entity'] = _('Área')
        context['list_url'] = reverse_lazy('configuracion:companyarea_list')
        context['action'] = 'add'
        return context


class CompanyAreaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'base.change_companyarea'
    model = CompanyArea
    template_name = 'core/form.html'
    form_class = CompanyAreaForm
    success_message = _("Área actualizada con éxito")
    
    def get_success_url(self):
        return reverse_lazy('configuracion:companyarea_list')
    
    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        
        # La auditoría de actualización se realizará automáticamente mediante las señales
        
        response = super().form_valid(form)
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': self.success_message,
                'redirect': self.get_success_url().resolve(self.request)
            })
        
        return response
    
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
        context['title'] = _('Actualizar Área')
        context['entity'] = _('Área')
        context['list_url'] = reverse_lazy('configuracion:companyarea_list')
        context['action'] = 'edit'
        return context


class CompanyAreaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'base.delete_companyarea'
    model = CompanyArea
    template_name = 'core/del.html'
    context_object_name = 'area'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Área')
        context['entity'] = _('Área')
        context['texto'] = f'¿Seguro de eliminar el Área {self.object.name} de {self.object.company}?'
        context['list_url'] = self.get_success_url()
        return context
    
    def get_success_url(self):
        return reverse_lazy('configuracion:companyarea_list')
    
    def delete(self, request, *args, **kwargs):
        area = self.get_object()
        success_message = _(f'Área "{area.name}" eliminada exitosamente')
        
        # Guardar datos importantes antes de eliminar
        area_name = area.name
        area_id = area.pk
        area.delete()
        try:
            area.delete()          
            messages.success(request, success_message)
            return HttpResponseRedirect(self.get_success_url())
            
        except ProtectedError:
            error_message = _('No se puede eliminar el área porque está siendo utilizada en otros registros')
            messages.error(request, error_message)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=400)
            return HttpResponseRedirect(self.get_success_url())
            
        except Exception as e:
            error_message = _(f'Ocurrió un error al eliminar el área: {str(e)}')
            messages.error(request, error_message)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=500)
            return HttpResponseRedirect(self.get_success_url())
    
    def post(self, request, *args, **kwargs):
        # Manejo consistente para peticiones AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                return self.delete(request, *args, **kwargs)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=500)
        return super().post(request, *args, **kwargs)


class CompanyAreaImportView(GenericCSVImportView):
    model = CompanyArea
    form_class = CompanyAreaForm
    success_url = reverse_lazy('configuracion:companyarea_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Importar Áreas')
        context['entity'] = _('Área')
        context['list_url'] = self.success_url
        return context
    
    def clean_row_data(self, row):
        """
        Sobrescribimos este método para manejar conversiones específicas
        para el modelo CompanyArea
        """
        cleaned_data = super().clean_row_data(row)
        
        # Si tenemos el nombre de la compañía en lugar del ID
        if 'company' in cleaned_data and not cleaned_data['company'].isdigit():
            try:
                company = Company.objects.get(name=cleaned_data['company'])
                cleaned_data['company'] = company.id
            except Company.DoesNotExist:
                # Crear log o manejar el error según sea necesario
                pass
                    
        return cleaned_data


class CompanyAreaExportView(GenericExportView):
    model = CompanyArea
    fields = ['company__name', 'name', 'description', 'default_manager__username']
    field_labels = {
        'company__name': 'Empresa',
        'name': 'Nombre',
        'description': 'Descripción',
        'default_manager__username': 'Responsable'
    }
    permission_required = 'base.view_companyarea'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar formatos disponibles
        context['export_formats'] = [
            {'format': 'csv', 'label': 'CSV'},
            {'format': 'pdf', 'label': 'PDF'},
            {'format': 'excel', 'label': 'Excel'}
        ]
        
        return context


def get_companyarea_details(request):
    """
    Vista para obtener información detallada de un área de la empresa.

    Args:
        request: HttpRequest con area_id en GET

    Returns:
        JsonResponse con información detallada del área y datos adicionales

    Raises:
        404: Si el área no existe
        400: Si no se proporciona area_id
    """
    area_id = request.GET.get('area_id')

    if not area_id:
        return JsonResponse({
            'status': 'error',
            'error': 'ID de área no proporcionado',
            'code': 'AREA_ID_REQUIRED'
        }, status=400)

    try:
        # Obtener el área usando get_object_or_404
        area = get_object_or_404(CompanyArea, pk=area_id)

        # Construir respuesta con datos del área
        area_data = {
            'status': 'success',
            'area': {
                'id': area.id,
                'empresa': area.company.name,
                'nombre': area.name,
                'descripcion': area.description,
                'responsable': area.default_manager.get_full_name() if area.default_manager else None,
                'metadata': {
                    'fecha_creacion': area.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(area, 'created_at') else None,
                    'ultima_actualizacion': area.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(area, 'updated_at') else None,
                    'creado_por': area.created_by.get_full_name() if hasattr(area, 'created_by') and area.created_by else None
                }
            }
        }

        # Agregamos información adicional si existe
        if hasattr(area, 'employees'):
            empleados = []
            for empleado in area.employees.all():
                empleados.append({
                    'id': empleado.id,
                    'nombre': empleado.get_full_name(),
                    'cargo': empleado.job_title if hasattr(empleado, 'job_title') else None,
                    'email': empleado.email
                })
            area_data['area']['empleados'] = empleados

        return JsonResponse(area_data)

    except CompanyArea.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'error': 'Área no encontrada',
            'code': 'AREA_NOT_FOUND'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': f'Error inesperado: {str(e)}',
            'code': 'UNEXPECTED_ERROR'
        }, status=500)