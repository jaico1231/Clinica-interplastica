from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from datetime import datetime, timedelta

from apps.audit.models import AuditLog

class AuditLogListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista para mostrar los registros de auditoría con filtros avanzados.
    """
    model = AuditLog
    template_name = 'audit/audit_log_list.html'
    permission_required = 'audit.view_auditlog'
    paginate_by = 50
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """
        Filtra los registros de AuditLog según los parámetros de la solicitud.
        """
        queryset = super().get_queryset()
        
        # Obtener filtros de la solicitud
        filters = self.request.GET.dict()
        
        # Filtro por modelo/tabla
        model_filter = filters.get('model')
        if model_filter:
            app_label, model_name = model_filter.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model_name.lower())
            queryset = queryset.filter(content_type=content_type)
        
        # Filtro por tipo de acción
        action_filter = filters.get('action')
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        # Filtro por usuario
        user_filter = filters.get('user')
        if user_filter:
            queryset = queryset.filter(user_id=user_filter)
        
        # Filtro por objeto específico
        object_id_filter = filters.get('object_id')
        if object_id_filter:
            queryset = queryset.filter(object_id=object_id_filter)
        
        # Filtro por fecha
        date_start = filters.get('date_start')
        date_end = filters.get('date_end')
        
        if date_start:
            try:
                date_start = datetime.strptime(date_start, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__gte=date_start)
            except ValueError:
                pass
        
        if date_end:
            try:
                date_end = datetime.strptime(date_end, '%Y-%m-%d')
                # Añadir un día para incluir todo el día final
                date_end = date_end + timedelta(days=1)
                queryset = queryset.filter(timestamp__lt=date_end)
            except ValueError:
                pass
        
        # Filtro de período predefinido
        period = filters.get('period')
        today = datetime.now()
        if period == 'today':
            queryset = queryset.filter(
                timestamp__gte=today.replace(hour=0, minute=0, second=0),
                timestamp__lt=(today + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            )
        elif period == 'yesterday':
            yesterday = today - timedelta(days=1)
            queryset = queryset.filter(
                timestamp__gte=yesterday.replace(hour=0, minute=0, second=0),
                timestamp__lt=today.replace(hour=0, minute=0, second=0)
            )
        elif period == 'week':
            start_of_week = today - timedelta(days=today.weekday())
            queryset = queryset.filter(
                timestamp__gte=start_of_week.replace(hour=0, minute=0, second=0)
            )
        elif period == 'month':
            start_of_month = today.replace(day=1, hour=0, minute=0, second=0)
            queryset = queryset.filter(timestamp__gte=start_of_month)
        
        # Búsqueda de texto
        search_query = filters.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(description__icontains=search_query) |
                Q(object_id__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(ip_address__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Añade información adicional al contexto para los filtros y la visualización.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _('Registros de Auditoría')
        
        # Modelos auditados (obtenidos de AUDIT_MODELS en settings.py)
        from django.conf import settings
        
        context['audit_models'] = []
        for model_path in getattr(settings, 'AUDIT_MODELS', []):
            try:
                app_label, model_name = model_path.split('.')
                model_class = apps.get_model(app_label, model_name)
                context['audit_models'].append({
                    'id': model_path,
                    'name': model_class._meta.verbose_name
                })
            except (ValueError, LookupError):
                continue
        
        # Tipos de acciones
        context['action_types'] = [
            {'id': 'CREATE', 'name': _('Creación')},
            {'id': 'UPDATE', 'name': _('Modificación')},
            {'id': 'DELETE', 'name': _('Eliminación')},
            {'id': 'LOGIN', 'name': _('Inicio de sesión')},
            {'id': 'LOGOUT', 'name': _('Cierre de sesión')},
            {'id': 'VIEW', 'name': _('Visualización')},
            {'id': 'OTHER', 'name': _('Otra acción')}
        ]
        
        # Períodos predefinidos
        context['periods'] = [
            {'id': 'today', 'name': _('Hoy')},
            {'id': 'yesterday', 'name': _('Ayer')},
            {'id': 'week', 'name': _('Esta semana')},
            {'id': 'month', 'name': _('Este mes')},
        ]
        
        # Usuarios que han realizado acciones
        User = apps.get_model(settings.AUTH_USER_MODEL.split('.')[0], settings.AUTH_USER_MODEL.split('.')[1])
        context['users'] = User.objects.filter(
            id__in=AuditLog.objects.values_list('user_id', flat=True).distinct()
        ).order_by('username')
        
        # Guardar los filtros actuales para mantener el estado en la UI
        context['current_filters'] = self.request.GET.dict()
        
        return context