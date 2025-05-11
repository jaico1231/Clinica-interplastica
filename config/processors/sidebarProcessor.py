from pathlib import Path
import glob
#menu por base de datos
from apps.base.models.menu import Menu, MenuItem


def sidebar_context(request):
    menus = Menu.objects.filter(is_active=True)
    menu_items = MenuItem.objects.filter(is_active=True)

    # Filtrar menús según los permisos del usuario
    if not request.user.is_superuser:
        user_groups = request.user.groups.all()
        menus = menus.filter(group__in=user_groups)

    return {
        'menus': menus,
        'menu_items': menu_items
    }

