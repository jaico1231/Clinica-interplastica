from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin # Opcional: para permisos
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages # Para feedback al usuario
from django.utils.translation import gettext_lazy as _
from apps.base.views.genericlistview import OptimizedSecureListView
from apps.notifications.forms.configure import WhatsAppConfigurationForm
from apps.notifications.models.emailmodel import WhatsAppConfiguration
from apps.notifications.views.email_configure import SuccessMessageMixin

# --- WhatsApp Configuration Views ---

class WhatsAppConfigurationListView(LoginRequiredMixin, ListView):
    model = WhatsAppConfiguration
    template_name = 'notifications/config/whatsapp_list.html'
    context_object_name = 'configurations'
    paginate_by = 15

class WhatsAppConfigurationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = WhatsAppConfiguration
    form_class = WhatsAppConfigurationForm
    template_name = 'notifications/config/whatsapp_form.html'
    success_url = reverse_lazy('notifications:whatsapp_config_list')
    success_message = "WhatsApp configuration created successfully."

class WhatsAppConfigurationUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = WhatsAppConfiguration
    form_class = WhatsAppConfigurationForm
    template_name = 'notifications/config/whatsapp_form.html'
    success_url = reverse_lazy('notifications:whatsapp_config_list')
    success_message = "WhatsApp configuration updated successfully."

class WhatsAppConfigurationDeleteView(LoginRequiredMixin, DeleteView):
    model = WhatsAppConfiguration
    template_name = 'notifications/config/confirm_delete.html'
    success_url = reverse_lazy('notifications:whatsapp_config_list')
    success_message = "WhatsApp configuration deleted successfully."

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)