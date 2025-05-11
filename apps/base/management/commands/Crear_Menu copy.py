#Crear_Menu
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.urls import get_resolver, URLPattern, URLResolver
from apps.base.models import Menu, MenuItem

class Command(BaseCommand):
    help = 'Crea o actualiza menús y elementos de menú automáticamente'
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando sincronización de menús...'))
        
        # Obtener o crear grupo administrador
        admin_group, _ = Group.objects.get_or_create(name='Administrador')
        
        # Procesar todas las URLs del proyecto
        urlconf = get_resolver()
        self.process_url_patterns(urlconf.url_patterns, admin_group)
        
        self.stdout.write(self.style.SUCCESS('Proceso de sincronización completado'))

    def process_url_patterns(self, url_patterns, admin_group, prefix='', current_app=None):
        for pattern in url_patterns:
            if isinstance(pattern, URLResolver):
                new_app = pattern.app_name or current_app
                new_prefix = f"{prefix}{pattern.namespace}:" if pattern.namespace else prefix
                self.process_url_patterns(
                    pattern.url_patterns,
                    admin_group,
                    new_prefix,
                    new_app
                )
            elif isinstance(pattern, URLPattern):
                self.process_url_pattern(pattern, admin_group, prefix, current_app)

    def process_url_pattern(self, pattern, admin_group, prefix, current_app):
        menu_name = getattr(pattern.callback, 'menu_name', None)
        menu_icon = getattr(pattern.callback, 'icon', 'file')
        
        if pattern.name and menu_name and current_app:
            app_name = self.clean_app_name(current_app)
            self.sync_menu(app_name, admin_group, menu_name, menu_icon, prefix, pattern)

    def clean_app_name(self, app_name):
        """Normaliza el nombre de la aplicación"""
        cleaned_name = app_name.upper()
        return 'ADMINISTRACION' if cleaned_name == 'SHARED' else cleaned_name

    def sync_menu(self, app_name, admin_group, menu_name, menu_icon, prefix, pattern):
        """Sincroniza un elemento del menú con la base de datos"""
        # Actualizar o crear menú principal
        menu, menu_created = Menu.objects.update_or_create(
            name=app_name,
            defaults={'icon': 'folder'}
        )
        menu.group.add(admin_group)

        # Actualizar o crear ítem del menú
        url_name = f'{prefix}{pattern.name}'
        menu_item, item_created = MenuItem.objects.update_or_create(
            menu=menu,
            name=menu_name,
            defaults={
                'url_name': url_name,
                'icon': menu_icon,
                'order': getattr(pattern.callback, 'menu_order', 0)
            }
        )
        menu_item.groups.add(admin_group)

        # Generar mensaje de log detallado
        self.log_sync_action(app_name, menu_name, menu_created, item_created)

    def log_sync_action(self, app_name, menu_name, menu_created, item_created):
        """Registra los resultados de la sincronización"""
        action_map = {
            (True, True): ('Menú creado', 'Ítem creado'),
            (False, True): ('', 'Ítem creado'),
            (True, False): ('Menú actualizado', ''),
            (False, False): ('', 'Ítem actualizado')
        }
        
        menu_action, item_action = action_map[(menu_created, item_created)]
        
        if menu_action:
            self.stdout.write(self.style.SUCCESS(f'{menu_action}: {app_name}'))
        if item_action:
            self.stdout.write(self.style.SUCCESS(f'{item_action}: {menu_name}'))
# class Command(BaseCommand):
#     help = 'Crea menús y elementos de menú automáticamente basados en las vistas y decoradores'

#     def handle(self, *args, **kwargs):
#         self.stdout.write(self.style.SUCCESS('Iniciando creación automática de menús...'))
        
#         # Crear grupo administrador
#         admin_group, _ = Group.objects.get_or_create(name='Administrador')
        
#         # Procesar las URLs
#         urlconf = get_resolver()
#         self.process_url_patterns(urlconf.url_patterns, admin_group)
        
#         self.stdout.write(self.style.SUCCESS('Proceso de creación de menús completado'))

#     def process_url_patterns(self, url_patterns, admin_group, prefix='', current_app=None):
#         for pattern in url_patterns:
#             if isinstance(pattern, URLResolver):
#                 # Obtener app_name del URLResolver
#                 new_app = pattern.app_name if pattern.app_name else current_app
#                 new_prefix = f"{prefix}{pattern.namespace}:" if pattern.namespace else prefix
#                 self.process_url_patterns(
#                     pattern.url_patterns,
#                     admin_group,
#                     new_prefix,
#                     new_app
#                 )
            
#             elif isinstance(pattern, URLPattern):
#                 self.process_url_pattern(pattern, admin_group, prefix, current_app)

#     def process_url_pattern(self, pattern, admin_group, prefix, current_app):
#         menu_name = getattr(pattern.callback, 'menu_name', None)
#         menu_icon = getattr(pattern.callback, 'icon', None)
        
#         if pattern.name and menu_name and current_app:
#             # Usar app_name de la URL
#             app_name = current_app.upper()
            
#             # Ajustes especiales de nombres
#             if app_name == 'SHARED':
#                 app_name = 'ADMINISTRACION'
            
#             # Crear/actualizar menú principal
#             menu, _ = Menu.objects.update_or_create(
#                 name=app_name,
#                 defaults={'icon': 'folder'}
#             )
#             menu.group.add(admin_group)
            
#             # Crear elemento de menú
#             url_name = f'{prefix}{pattern.name}'
#             menu_item, created = MenuItem.objects.update_or_create(
#                 menu=menu,
#                 name=menu_name,
#                 defaults={
#                     'url_name': url_name,
#                     'icon': menu_icon or 'file'
#                 }
#             )
#             menu_item.groups.add(admin_group)
            
#             # Log de resultados
#             action = 'Creado' if created else 'Actualizado'
#             log_message = f'{action} MenuItem: {menu_name} en Menú: {app_name}'
#             self.stdout.write(self.style.SUCCESS(log_message))