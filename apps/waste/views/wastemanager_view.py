from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum

from apps.waste.forms.waste_form import WasteManagerForm
from apps.waste.models.waste_model import WasteDestination, WasteManager
# from apps.waste.models import WasteManager, WasteDestination


class WasteManagerListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista para listar gestores de residuos con capacidades de búsqueda
    y filtrado.
    """
    permission_required = 'waste.view_wastemanager'
    model = WasteManager
    template_name = 'core/list.html'
    context_object_name = 'objects'
    paginate_by = 20
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['name', 'tax_id', 'city', 'environmental_license']
    # Ordenamiento por defecto
    ordering = ['name']
    
    # Atributos específicos
    title = _('Listado de Gestores de Residuos')
    entity = _('Gestor de Residuos')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por ciudad
        city = self.request.GET.get('city', '')
        if city:
            queryset = queryset.filter(city__iexact=city)
        
        # Filtrar por estado de actividad
        is_active = self.request.GET.get('is_active', '')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
            
        # Búsqueda general
        search = self.request.GET.get('search', '')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(tax_id__icontains=search) | 
                Q(city__icontains=search) |
                Q(environmental_license__icontains=search)
            )
            
        # Anotaciones de número de destinos asociados
        queryset = queryset.annotate(destination_count=Count('wastedestination'))
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['NOMBRE', 'NIT', 'CIUDAD', 'TELÉFONO', 'EMAIL', 'LICENCIA', 'DESTINOS', 'ESTADO']
        context['fields'] = ['name', 'tax_id', 'city', 'phone', 'email', 'environmental_license', 'destination_count', 'is_active']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': _('Nuevo Gestor'),
                'icon': 'add',
                'url': 'control residuos:waste_create',
                'modal': True,
            }
        ]
        
        context['actions'] = [
            {
                'name': 'view',
                'label': '',
                'icon': 'visibility',
                'color': 'info',
                'color2': 'white',
                'title': _('Ver Gestor'),
                'url': 'control residuos:waste_detail',
                'modal': False
            },
            {
                'name': 'edit',
                'label': '',
                'icon': 'edit',
                'color': 'primary',
                'color2': 'white',
                'title': _('Editar Gestor'),
                'url': 'control residuos:waste_update',
                'modal': True
            },
            {
                'name': 'del',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'title': _('Eliminar Gestor'),
                'url': 'control residuos:waste_delete',
                'modal': True
            },
        ]
        
        # Listado de ciudades para el filtro
        context['cities'] = WasteManager.objects.values_list('city', flat=True).distinct().order_by('city')
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('control residuos:waste_waste_manager_list')
        
        return context


class WasteManagerDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Mostrar detalles del gestor de residuos"""
    permission_required = 'waste.view_wastemanager'
    model = WasteManager
    context_object_name = 'manager'
    template_name = 'waste/manager_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Detalle de Gestor de Residuos')
        context['entity'] = _('Gestor de Residuos')
        
        # Obtener destinos relacionados con este gestor
        context['destinations'] = WasteDestination.objects.filter(
            manager=self.object
        ).order_by('-departure_date')[:10]  # Mostrar los 10 más recientes
        
        # Estadísticas básicas 
        stats = WasteDestination.objects.filter(manager=self.object).aggregate(
            total_destinos=Count('id'),
            total_cantidad=Sum('quantity')
        )
        context['stats'] = stats
        
        # Obtener conteo por método de tratamiento
        treatment_stats = WasteDestination.objects.filter(manager=self.object).values(
            'treatment_method'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Convertir códigos de método a nombres legibles
        treatment_methods_dict = dict(WasteDestination.TREATMENT_METHODS)
        for stat in treatment_stats:
            stat['name'] = treatment_methods_dict.get(stat['treatment_method'], stat['treatment_method'])
        
        context['treatment_stats'] = treatment_stats
        
        # Agregar URLs para acciones
        context['edit_url'] = reverse('control residuos:manager_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse('control residuos:manager_delete', kwargs={'pk': self.object.pk})
        context['list_url'] = reverse('control residuos:waste_manager_list')
        
        return context


class WasteManagerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear un nuevo gestor de residuos
    """
    permission_required = 'waste.add_wastemanager'
    model = WasteManager
    form_class = WasteManagerForm
    template_name = 'core/create.html'
    
    def get_success_url(self):
        return reverse_lazy('control residuos:waste_manager_list')
    
    def form_valid(self, form):
        self.object = form.save()
        
        messages.success(self.request, _('Gestor de residuos creado con éxito'))
        
        # Verificar si es una solicitud AJAX
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Gestor de residuos creado con éxito'),
                'redirect': self.get_success_url()
            })
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
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
        context['title'] = _('Registrar Gestor de Residuos')
        context['entity'] = _('Gestor de Residuos')
        context['list_url'] = reverse_lazy('control residuos:waste_manager_list')
        context['action'] = 'add'
        return context


class WasteManagerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para actualizar información de un gestor de residuos
    """
    permission_required = 'waste.change_wastemanager'
    model = WasteManager
    form_class = WasteManagerForm
    template_name = 'core/create.html'
    
    def get_success_url(self):
        return reverse_lazy('control residuos:waste_manager_list')
    
    def form_valid(self, form):
        self.object = form.save()
        
        messages.success(self.request, _('Gestor de residuos actualizado con éxito'))
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Gestor de residuos actualizado con éxito'),
                'redirect': self.get_success_url()
            })
            
        return super().form_valid(form)
    
    def form_invalid(self, form):
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
        context['title'] = _('Editar Gestor de Residuos')
        context['entity'] = _('Gestor de Residuos')
        context['list_url'] = reverse_lazy('control residuos:waste_manager_list')
        context['action'] = 'edit'
        return context


class WasteManagerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Vista para eliminar un gestor de residuos
    Incluye verificación de referencias antes de eliminar
    """
    permission_required = 'waste.delete_wastemanager'
    model = WasteManager
    template_name = 'core/delete.html'
    
    def get_success_url(self):
        return reverse_lazy('control residuos:waste_manager_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Gestor de Residuos')
        context['entity'] = _('Gestor de Residuos')
        context['list_url'] = reverse_lazy('control residuos:waste_manager_list')
        
        # Verificar si este gestor tiene destinos asociados
        destinations_count = WasteDestination.objects.filter(manager=self.object).count()
        context['has_related'] = destinations_count > 0
        context['related_message'] = _(
            'Este gestor no puede ser eliminado porque tiene {} destinos asociados. '
            'Considere marcarlo como inactivo en lugar de eliminarlo.'
        ).format(destinations_count)
        
        return context
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Verificar si tiene registros asociados antes de eliminar
        destinations_count = WasteDestination.objects.filter(manager=self.object).count()
        
        if destinations_count > 0:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': _(
                        'Este gestor no puede ser eliminado porque tiene {} destinos asociados. '
                        'Considere marcarlo como inactivo en lugar de eliminarlo.'
                    ).format(destinations_count)
                }, status=400)
            else:
                messages.error(
                    request, 
                    _(
                        'Este gestor no puede ser eliminado porque tiene {} destinos asociados. '
                        'Considere marcarlo como inactivo en lugar de eliminarlo.'
                    ).format(destinations_count)
                )
                return self.render_to_response(self.get_context_data())
        
        success_url = self.get_success_url()
        self.object.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Gestor de residuos eliminado con éxito'),
                'redirect': success_url
            })
        
        messages.success(request, _('Gestor de residuos eliminado con éxito'))
        return self.get_success_url()