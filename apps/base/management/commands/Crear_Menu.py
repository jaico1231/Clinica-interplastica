from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.urls import get_resolver, URLPattern, URLResolver
from django.utils.module_loading import import_string
from apps.base.models import Menu, MenuItem
import importlib

class Command(BaseCommand):
    help = 'Crea o actualiza menús y elementos de menú automáticamente'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando sincronización de menús...'))
        admin_group, _ = Group.objects.get_or_create(name='Administrador')
        urlconf = get_resolver()
        self.process_url_patterns(urlconf.url_patterns, admin_group)
        self.stdout.write(self.style.SUCCESS('Proceso de sincronización completado'))

    def process_url_patterns(self, url_patterns, admin_group, prefix='', current_app=None, url_module=None):
        for pattern in url_patterns:
            if isinstance(pattern, URLResolver):
                new_app = pattern.app_name or current_app
                new_prefix = f"{prefix}{pattern.namespace}:" if pattern.namespace else prefix
                new_url_module = pattern.urlconf_module if hasattr(pattern, 'urlconf_module') else url_module
                self.process_url_patterns(
                    pattern.url_patterns,
                    admin_group,
                    new_prefix,
                    new_app,
                    new_url_module
                )
            elif isinstance(pattern, URLPattern):
                self.process_url_pattern(pattern, admin_group, prefix, current_app, url_module)

    def process_url_pattern(self, pattern, admin_group, prefix, current_app, url_module):
        menu_name = getattr(pattern.callback, 'menu_name', None)
        menu_icon = getattr(pattern.callback, 'icon', None)
        
        if pattern.name and menu_name and current_app and url_module:
            app_icon = self.get_app_icon(url_module)
            menu = self.get_or_create_app_menu(current_app, admin_group, app_icon)
            url_name = f'{prefix}{pattern.name}'
            self.create_menu_item(menu, menu_name, menu_icon, url_name, admin_group)

    def get_app_icon(self, url_module):
        """Obtiene el icono de la aplicación desde el módulo de URLs"""
        try:
            return url_module.app_icon
        except AttributeError:
            return 'folder'  # Valor por defecto

    def get_or_create_app_menu(self, app_name, admin_group, app_icon):
        """Actualizado para usar el app_icon"""
        if '.' in app_name:
            app_parts = app_name.split('.')
            app_name = app_parts[-1]
        
        menu_name = app_name.upper()
        
        menu, created = Menu.objects.update_or_create(
            name=menu_name,
            defaults={'icon': app_icon}
        )
        
        menu.group.add(admin_group)
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Menú creado: {menu_name} (Icono: {app_icon})'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Menú actualizado: {menu_name} (Nuevo icono: {app_icon})'))
        
        return menu

    def create_menu_item(self, menu, menu_name, menu_icon, url_name, admin_group):
        menu_item, created = MenuItem.objects.update_or_create(
            menu=menu,
            name=menu_name,
            defaults={
                'url_name': url_name,
                'icon': menu_icon or 'article',
                'is_active': True
            }
        )
        
        menu_item.groups.add(admin_group)
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Ítem creado: {menu_name} → {url_name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  Ítem actualizado: {menu_name} → {url_name}'))