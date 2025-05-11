# apps/base/templatetags/menu_decorador.py
# apps/base/templatetags/menu_decorador.py
from functools import wraps

def add_menu_name(menu_name, icon=None):
    """
    Decorador para agregar información de menú a una vista de Django.
    
    Args:
        menu_name (str): Nombre que se mostrará en el menú
        icon (str): Nombre del icono de Material Design o Font Awesome
    
    Returns:
        function: Función decoradora que agrega atributos al objeto vista
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            return view_func(*args, **kwargs)
        
        # Agregar atributos al objeto vista
        _wrapped_view.menu_name = menu_name
        _wrapped_view.icon = icon
        
        return _wrapped_view
    return decorator

def register_menu_app(app_name, icon, menu_groups=None):
    """
    Función para usar en urls.py para registrar una aplicación en el sistema de menús
    
    Args:
        app_name (str): Nombre de la aplicación/módulo
        icon (str): Ícono predeterminado para la aplicación
        menu_groups (list|str): Grupos que pueden ver este menú
    
    Returns:
        dict: Configuración del menú para esta aplicación
    """
    return {
        'app_name': app_name,
        'icon': icon,
        'menu_groups': menu_groups if menu_groups else 'ADMINISTRACION'
    }