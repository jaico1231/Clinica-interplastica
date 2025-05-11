from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
import json

from apps.audit.models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_display', 'action_display', 'table_name', 'object_id', 'ip_address', 'short_description')
    list_filter = ('action', 'timestamp', 'table_name', 'user')
    search_fields = ('user__username', 'table_name', 'description', 'object_id', 'ip_address')
    readonly_fields = (
        'user', 'action', 'timestamp', 'ip_address', 'user_agent',
        'content_type', 'object_id', 'table_name',
        'data_before_pretty', 'data_after_pretty',
        'description'
    )
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (_('Información básica'), {
            'fields': ('action', 'timestamp', 'user', 'description')
        }),
        (_('Información del objeto'), {
            'fields': ('content_type', 'object_id', 'table_name')
        }),
        (_('Datos'), {
            'fields': ('data_before_pretty', 'data_after_pretty')
        }),
        (_('Información de cliente'), {
            'fields': ('ip_address', 'user_agent')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Solo superusuarios pueden eliminar registros de auditoría
        return request.user.is_superuser
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.username}"
        return _("Sistema")
    user_display.short_description = _('Usuario')
    
    def action_display(self, obj):
        actions_colors = {
            'CREATE': 'success',
            'UPDATE': 'primary',
            'DELETE': 'danger',
            'LOGIN': 'info',
            'LOGOUT': 'secondary',
            'VIEW': 'light',
            'OTHER': 'warning'
        }
        color = actions_colors.get(obj.action, 'dark')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_action_display()
        )
    action_display.short_description = _('Acción')
    
    def short_description(self, obj):
        if obj.description:
            max_length = 50
            if len(obj.description) > max_length:
                return f"{obj.description[:max_length]}..."
            return obj.description
        return "-"
    short_description.short_description = _('Descripción')
    
    def data_before_pretty(self, obj):
        if obj.data_before:
            return format_html(
                '<pre style="max-height:300px;overflow-y:auto;">{}</pre>',
                json.dumps(obj.data_before, indent=2, ensure_ascii=False)
            )
        return "-"
    data_before_pretty.short_description = _('Datos anteriores')
    
    def data_after_pretty(self, obj):
        if obj.data_after:
            return format_html(
                '<pre style="max-height:300px;overflow-y:auto;">{}</pre>',
                json.dumps(obj.data_after, indent=2, ensure_ascii=False)
            )
        return "-"
    data_after_pretty.short_description = _('Datos nuevos')