from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from apps.base.forms.companyform import CompanyForm
from apps.base.models.company import Company, CompanyArea

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

class AreaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = CompanyArea
    template_name = 'core/list.html'
    permission_required = 'base.view_company'

    search_fields = []
    order_by=()
    