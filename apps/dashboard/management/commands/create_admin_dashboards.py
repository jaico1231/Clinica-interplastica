# apps/dashboard/management/commands/create_admin_dashboards.py
from django.core.management.base import BaseCommand
from apps.dashboard.services.dashboard_creator import create_admin_dashboards, apply_admin_permissions_to_dashboards

class Command(BaseCommand):
    help = 'Crea dashboards predefinidos para el grupo de administradores'

    def handle(self, *args, **kwargs):
        try:
            create_admin_dashboards()
            apply_admin_permissions_to_dashboards()
            self.stdout.write(self.style.SUCCESS('Dashboards para administradores creados exitosamente'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al crear dashboards: {str(e)}'))