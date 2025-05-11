# apps/base/templatetags/menu_tags.py
from django import template
from django.urls import resolve, reverse
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """Verifica si un usuario pertenece a un grupo específico"""
    try:
        group = Group.objects.get(name=group_name)
        return group in user.groups.all()
    except Group.DoesNotExist:
        return False

@register.inclusion_tag('components/sidebar_menu.html', takes_context=True)
def render_menu(context):
    """
    Renderiza el menú completo basado en la configuración de las URLs y permisos de usuario
    """
    request = context['request']
    user = request.user
    
    # Obtener la vista actual
    current_url_name = resolve(request.path_info).url_name
    
    # Construir la estructura del menú desde las aplicaciones registradas
    menu_structure = build_menu_structure(user)
    
    return {
        'menus': menu_structure,
        'request': request,
        'current_url_name': current_url_name
    }

def build_menu_structure(user):
    """
    Construye la estructura del menú basada en las aplicaciones y URLs configuradas
    Agrega automáticamente los iconos definidos en las configuraciones de URL
    """
    from django.apps import apps
    from importlib import import_module
    
    menu_structure = []
    
    # Recorrer todas las aplicaciones instaladas
    for app_config in apps.get_app_configs():
        try:
            # Intentar importar el módulo urls de la aplicación
            urls_module = import_module(f"{app_config.name}.urls")
            
            # Verificar si el módulo tiene configuración de menú
            if hasattr(urls_module, 'app_name') and hasattr(urls_module, 'icon'):
                menu_item = {
                    'name': getattr(urls_module, 'app_name', '').capitalize(),
                    'icon': getattr(urls_module, 'icon', 'settings'),  # Icono predeterminado
                    'is_active': True,
                    'items': [],
                    'group': get_menu_groups(urls_module)
                }
                
                # Agregar items del menú desde las URLs con decoradores
                for pattern in urls_module.urlpatterns:
                    view = getattr(pattern.callback, 'view_class', pattern.callback)
                    
                    # Comprobar si la vista tiene atributos de menú
                    if hasattr(view, 'menu_name'):
                        item = {
                            'name': view.menu_name,
                            'icon': getattr(view, 'icon', None),
                            'url_name': f"{urls_module.app_name}:{pattern.name}",
                            'is_active': True,
                            'groups': get_view_groups(view)
                        }
                        menu_item['items'].append(item)
                
                # Solo agregar menús con elementos
                if menu_item['items']:
                    menu_structure.append(menu_item)
                    
        except (ImportError, AttributeError):
            # Ignorar aplicaciones sin configuración de menú
            pass
    
    return menu_structure

def get_menu_groups(urls_module):
    """Obtiene los grupos asociados con un menú completo"""
    menu_groups = getattr(urls_module, 'menu_groups', ['ADMINISTRACION'])
    if isinstance(menu_groups, str):
        menu_groups = [menu_groups]
    return [{'name': group} for group in menu_groups]

def get_view_groups(view):
    """Obtiene los grupos asociados con una vista específica"""
    view_groups = getattr(view, 'menu_group', ['ADMINISTRACION'])
    if isinstance(view_groups, str):
        view_groups = [view_groups]
    return [{'name': group} for group in view_groups]