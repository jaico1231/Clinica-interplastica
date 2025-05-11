# En apps/audit/urls.py
from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.base.templatetags.menu_decorador import add_menu_name
from apps.audit.views import AuditLogListView

app_name = 'auditoria'  # Define el nombre de la app para los templates y urls
app_icon= 'settings'


urlpatterns = [
    path('audit/', 
         login_required(add_menu_name('historial','manage_search')(AuditLogListView.as_view())), 
         name='audit_log_list'),
]

