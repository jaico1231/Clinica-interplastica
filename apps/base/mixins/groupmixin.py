from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from collections import defaultdict

class GroupViewMixin:
    """
    Mixin para proporcionar funcionalidades comunes a las vistas de grupos
    como obtener y organizar permisos.
    """
    
    def get_all_permissions(self):
        """
        Obtiene todos los permisos disponibles, excluyendo
        aplicaciones del sistema que no son relevantes para los usuarios.
        
        Returns:
            QuerySet: Permisos filtrados y ordenados
        """
        excluded_apps = ['admin', 'contenttypes', 'sessions', 'auth.logentry']
        
        # Obtener todos los permisos excluyendo aplicaciones del sistema
        return Permission.objects.exclude(
            content_type__app_label__in=excluded_apps
        ).select_related('content_type').order_by(
            'content_type__app_label', 'content_type__model', 'name'
        )
    
    def get_permissions_by_app(self, current_permissions=None):
        """
        Organiza los permisos por aplicación y modelo para una visualización jerárquica.
        
        Args:
            current_permissions (QuerySet, optional): Permisos actualmente asignados. Defaults to None.
        
        Returns:
            dict: Diccionario organizado con aplicaciones, modelos y permisos
        """
        if current_permissions is None:
            current_permissions = set()
        else:
            # Convertir a conjunto de IDs para comparación eficiente
            current_permissions = set(current_permissions.values_list('id', flat=True))
            
        permissions_by_app = defaultdict(lambda: defaultdict(list))
        
        # Obtener todos los tipos de contenido
        content_types = ContentType.objects.all().order_by('app_label', 'model')
        
        for content_type in content_types:
            app_label = content_type.app_label
            model_name = content_type.model
            
            # Excluir aplicaciones del sistema
            if app_label in ['admin', 'contenttypes', 'sessions']:
                continue
                
            # Verificar si el modelo existe
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                continue
                
            # Obtener permisos para este modelo
            perms = Permission.objects.filter(content_type=content_type)
            
            # Solo agregar si hay permisos
            if perms.exists():
                for perm in perms:
                    # Formatear el nombre del permiso para mejor legibilidad
                    friendly_name = self._get_friendly_permission_name(perm, model_name)
                    
                    permissions_by_app[app_label][model_name].append({
                        'id': perm.id,
                        'name': friendly_name,
                        'codename': perm.codename,
                        'selected': perm.id in current_permissions
                    })
        
        return dict(permissions_by_app)
    
    def _get_friendly_permission_name(self, permission, model_name=None):
        """
        Convierte el nombre del permiso a un formato más amigable.
        
        Args:
            permission (Permission): Objeto de permiso de Django
            model_name (str, optional): Nombre del modelo. Defaults to None.
        
        Returns:
            str: Nombre del permiso en formato amigable
        """
        # Mapa de acciones para mejor legibilidad
        action_map = {
            'add': 'Crear',
            'change': 'Modificar',
            'delete': 'Eliminar',
            'view': 'Ver',
        }
        
        # Obtener acción del permiso (add, change, delete, view)
        codename_parts = permission.codename.split('_')
        if len(codename_parts) > 1:
            action = codename_parts[0]
            if action in action_map:
                model = model_name or ' '.join(codename_parts[1:]).replace('_', ' ').title()
                return f"{action_map[action]} {model}"
        
        # Si no se puede simplificar, devolver el nombre original
        return permission.name
