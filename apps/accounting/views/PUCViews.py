from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext as _
from apps.accounting.models.PUC import (
    Naturaleza,
    GrupoCuenta,
    CuentaMayor,
    SubCuenta,
    CuentaDetalle,
    CuentaAuxiliar
)
from apps.accounting.forms.PUC_Forms import (
    NaturalezaForm,
    GrupoCuentaForm,
    CuentaMayorForm,
    SubCuentaForm,
    CuentaDetalleForm,
    CuentaAuxiliarForm
)

class PUCStructureListView(ListView):
    """
    Vista principal que muestra la estructura completa del PUC
    con todos sus niveles jerárquicos.
    """
    model = Naturaleza
    template_name = 'PUC.html'
    context_object_name = 'naturalezas'

    def get_queryset(self):
        """
        Optimiza la consulta con prefetch_related para cargar
        todos los niveles jerárquicos de una sola vez.
        """
        return Naturaleza.objects.prefetch_related(
            'grupos_cuenta',
            'grupos_cuenta__cuentas_mayor',
            'grupos_cuenta__cuentas_mayor__subcuentas',
            'grupos_cuenta__cuentas_mayor__subcuentas__cuentas_detalle',
            'grupos_cuenta__cuentas_mayor__subcuentas__cuentas_detalle__cuentas_auxiliares'
        ).all()
    
    def get_context_data(self, **kwargs):
        """
        Agrega datos adicionales al contexto para ser utilizados en la plantilla.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _('Plan Único de Cuentas')
        context['module'] = _('Contabilidad')
        return context


class PUCBaseView:
    """
    Clase base con métodos comunes para todas las vistas CRUD del PUC.
    """
    template_name = 'PUC_form.html'
    
    def get_success_url(self):
        """
        Retorna a la lista del PUC después de la operación exitosa.
        """
        return reverse_lazy('contabilidad:puc_list')
    
    def form_valid(self, form):
        """
        Procesa el formulario válido y responde según tipo de petición.
        """
        self.object = form.save()
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': self.success_message,
                'id': self.object.id,
                'nombre': str(self.object)
            })
        
        messages.success(self.request, self.success_message)
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """
        Maneja respuestas para formularios inválidos.
        """
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        messages.error(self.request, _('Por favor, corrija los errores en el formulario.'))
        return super().form_invalid(form)

class AllPucListView(ListView):
    model = GrupoCuenta
    template_name = "PUC/PUC_list.html"
    context_object_name = 'grupos_cuenta'

    def get_queryset(self):
        # Obtener todos los grupos de cuenta con sus relaciones anidadas
        return GrupoCuenta.objects.prefetch_related(
            'cuentas_mayor',
            'cuentas_mayor__subcuentas',
            'cuentas_mayor__subcuentas__cuentas_detalle',
            'cuentas_mayor__subcuentas__cuentas_detalle__cuentas_auxiliares'
        ).all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Opcionalmente, agregar conteos para cada nivel de cuenta
        context['total_grupos'] = GrupoCuenta.objects.count()
        context['total_cuentas_mayor'] = CuentaMayor.objects.count()
        context['total_subcuentas'] = SubCuenta.objects.count()
        context['total_cuentas_detalle'] = CuentaDetalle.objects.count()
        context['total_cuentas_auxiliares'] = CuentaAuxiliar.objects.count()
        
        # Si necesitas filtrar por empresa para las cuentas auxiliares
        # company_id = self.request.GET.get('company_id')
        # if company_id:
        #     context['company'] = get_object_or_404(Company, id=company_id)
        #     context['cuentas_auxiliares_filtradas'] = CuentaAuxiliar.objects.filter(company_id=company_id)
        
        return context
        

class PUCCreateBaseView(PUCBaseView, CreateView):
    """
    Clase base para las vistas de creación de elementos PUC.
    """
    
    def get(self, request, *args, **kwargs):
        """
        Prepara el formulario y contexto para peticiones GET.
        """
        form = self.get_form()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return self.render_form_response(form)
        
        return super().get(request, *args, **kwargs)
    
    def render_form_response(self, form):
        """
        Renderiza solo el formulario para peticiones AJAX.
        """
        context = {
            'form': form,
            'parent': getattr(self, 'parent_object', None),
            'action': 'create'
        }
        from django.template.loader import render_to_string
        form_html = render_to_string(self.template_name, context, self.request)
        return JsonResponse({'form_html': form_html})


class PUCUpdateBaseView(PUCBaseView, UpdateView):
    """
    Clase base para las vistas de actualización de elementos PUC.
    """
    
    def get(self, request, *args, **kwargs):
        """
        Prepara el formulario para actualizar un elemento existente.
        """
        self.object = self.get_object()
        form = self.get_form()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return self.render_form_response(form)
        
        return super().get(request, *args, **kwargs)
    
    def render_form_response(self, form):
        """
        Renderiza solo el formulario para peticiones AJAX.
        """
        context = {
            'form': form,
            'object': self.object,
            'action': 'update'
        }
        from django.template.loader import render_to_string
        form_html = render_to_string(self.template_name, context, self.request)
        return JsonResponse({'form_html': form_html})

# ---- Implementaciones específicas para cada nivel del PUC ----


class SubcuentaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vista para crear una nueva Subcuenta."""
    permission_required = 'accounting.add_subcuenta'
    model = SubCuenta
    form_class = SubCuentaForm
    template_name = 'core/create.html'

    def get_success_url(self):
        return reverse_lazy('contabilidad:puc_list')
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Subcuenta creada exitosamente'))
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Subcuenta creada exitosamente'),
                'id': self.object.id,
                'nombre': str(self.object)
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
        context['title'] = _('Crear Subcuenta')
        context['entity'] = _('Subcuenta')
        context['list_url'] = reverse_lazy('contabilidad:puc_list')
        context['action'] = 'add'
        return context

class SubcuentaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Vista para actualizar una Subcuenta existente."""
    permission_required = 'accounting.change_subcuenta'
    model = SubCuenta
    form_class = SubCuentaForm
    template_name = 'core/create.html'

    def get_success_url(self):
        return reverse_lazy('contabilidad:puc_list')
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Subcuenta actualizada exitosamente'))
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Subcuenta actualizada exitosamente'),
                'id': self.object.id,
                'nombre': str(self.object)
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
        context['title'] = _('Actualizar Subcuenta')
        context['entity'] = _('Subcuenta')
        context['list_url'] = reverse_lazy('contabilidad:puc_list')
        context['action'] = 'edit'
        return context

class SubcuentaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Vista para eliminar una Subcuenta existente."""
    permission_required = 'accounting.delete_subcuenta'
    model = SubCuenta
    template_name = 'core/del.html'

    def get_success_url(self):
        return reverse_lazy('contabilidad:puc_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, _('Subcuenta eliminada exitosamente'))
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Subcuenta eliminada exitosamente'),
                'id': self.object.id,
                'nombre': str(self.object)
            })
        
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Subcuenta')
        context['entity'] = _('Subcuenta')
        context['texto'] = _(f'¿Está seguro de eliminar la Subcuenta {self.object}?')
        context['list_url'] = reverse_lazy('contabilidad:puc_list')
        return context

# CRUD para CuentaDetalle
class CuentaDetalleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vista para crear una nueva Cuenta Detalle."""
    permission_required = 'accounting.add_cuentadetalle'
    model = CuentaDetalle
    form_class = CuentaDetalleForm
    template_name = 'core/create.html'

    def get_success_url(self):
        return reverse_lazy('contabilidad:puc_list')
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Cuenta Detalle creada exitosamente'))
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Cuenta Detalle creada exitosamente'),
                'id': self.object.id,
                'nombre': str(self.object)
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
        context['title'] = _('Crear Cuenta Detalle')
        context['entity'] = _('Cuenta Detalle')
        context['list_url'] = reverse_lazy('contabilidad:puc_list')
        context['action'] = 'add'
        return context

class CuentaDetalleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Vista para actualizar una Cuenta Detalle existente."""
    permission_required = 'accounting.change_cuentadetalle'
    model = CuentaDetalle
    form_class = CuentaDetalleForm
    template_name = 'core/create.html'

    def get_success_url(self):
        return reverse_lazy('contabilidad:puc_list')
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Cuenta Detalle actualizada exitosamente'))
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Cuenta Detalle actualizada exitosamente'),
                'id': self.object.id,
                'nombre': str(self.object)
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
        context['title'] = _('Actualizar Cuenta Detalle')
        context['entity'] = _('Cuenta Detalle')
        context['list_url'] = reverse_lazy('contabilidad:puc_list')
        context['action'] = 'edit'
        return context

class CuentaDetalleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Vista para eliminar una Cuenta Detalle existente."""
    permission_required = 'accounting.delete_cuentadetalle'
    model = CuentaDetalle
    template_name = 'core/del.html'

    def get_success_url(self):
        return reverse_lazy('contabilidad:puc_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()  # Elimina el objeto
        messages.success(request, _('Cuenta Detalle eliminada exitosamente'))
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Cuenta Detalle eliminada exitosamente'),
                'id': self.object.id,
                'nombre': str(self.object)
            })
        
        # Redirige manualmente sin llamar a super().delete()
        return HttpResponseRedirect(self.get_success_url())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Cuenta Detalle')
        context['entity'] = _('Cuenta Detalle')
        context['texto'] = _(f'¿Está seguro de eliminar la Cuenta Detalle {self.object}?')
        context['list_url'] = reverse_lazy('contabilidad:puc_list')
        return context

# CRUD para CuentaAuxiliar
class CuentaAuxiliarCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vista para crear una nueva Cuenta Auxiliar."""
    permission_required = 'accounting.add_cuentaauxiliar'
    model = CuentaAuxiliar
    form_class = CuentaAuxiliarForm
    template_name = 'core/create.html'

    def get_success_url(self):
        return reverse_lazy('contabilidad:puc_list')
    
    def form_valid(self, form):
        form.instance.company = self.request.user.company
        self.object = form.save()
        messages.success(self.request, _('Cuenta Auxiliar creada exitosamente'))
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Cuenta Auxiliar creada exitosamente'),
                'id': self.object.id,
                'nombre': str(self.object)
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
        context['title'] = _('Crear Cuenta Auxiliar')
        context['entity'] = _('Cuenta Auxiliar')
        context['list_url'] = reverse_lazy('contabilidad:puc_list')
        context['action'] = 'add'
        return context

class CuentaAuxiliarUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Vista para actualizar una Cuenta Auxiliar existente."""
    permission_required = 'accounting.change_cuentaauxiliar'
    model = CuentaAuxiliar
    form_class = CuentaAuxiliarForm
    template_name = 'core/create.html'

    def get_success_url(self):
        return reverse_lazy('contabilidad:puc_list')
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Cuenta Auxiliar actualizada exitosamente'))
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Cuenta Auxiliar actualizada exitosamente'),
                'id': self.object.id,
                'nombre': str(self.object)
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
        context['title'] = _('Actualizar Cuenta Auxiliar')
        context['entity'] = _('Cuenta Auxiliar')
        context['list_url'] = reverse_lazy('contabilidad:puc_list')
        context['action'] = 'edit'
        return context

class CuentaAuxiliarDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Vista para eliminar una Cuenta Auxiliar existente."""
    permission_required = 'accounting.delete_cuentaauxiliar'
    model = CuentaAuxiliar
    template_name = 'core/del.html'

    def get_success_url(self):
        return reverse_lazy('contabilidad:puc_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, _('Cuenta Auxiliar eliminada exitosamente'))
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Cuenta Auxiliar eliminada exitosamente'),
                'id': self.object.id,
                'nombre': str(self.object)
            })
        
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Cuenta Auxiliar')
        context['entity'] = _('Cuenta Auxiliar')
        context['list_url'] = reverse_lazy('contabilidad:puc_list')
        return context