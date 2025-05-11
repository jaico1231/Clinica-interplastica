#menu.py
from django.db import models
from django.contrib.auth.models import Group

class Menu(models.Model):
    """
    Modelo para representar un menú principal en la aplicación.
    Cada menú puede tener múltiples elementos de menú.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Nombre interno del menú")
    display_name = models.CharField(max_length=100, blank=True, help_text="Nombre para mostrar en la interfaz")
    icon = models.CharField(max_length=50, default="folder", help_text="Icono Material Design o Font Awesome")
    order = models.PositiveSmallIntegerField(default=0, help_text="Orden de aparición")
    is_active = models.BooleanField(default=True, help_text="Indica si el menú está activo")
    group = models.ManyToManyField(Group, blank=True, help_text="Grupos que pueden ver este menú")
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Menú"
        verbose_name_plural = "Menús"
    
    def __str__(self):
        return self.display_name or self.name
    
    def save(self, *args, **kwargs):
        # Si no hay nombre para mostrar, usar el nombre interno formateado
        if not self.display_name:
            self.display_name = self.name.replace('_', ' ').title()
        super().save(*args, **kwargs)


class MenuItem(models.Model):
    """
    Modelo para representar un elemento de menú que pertenece a un menú principal.
    """
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100, help_text="Nombre del elemento de menú")
    url_name = models.CharField(max_length=100, help_text="Nombre de URL para enlace")
    icon = models.CharField(max_length=50, blank=True, help_text="Icono Material Design o Font Awesome")
    order = models.PositiveSmallIntegerField(default=0, help_text="Orden de aparición")
    is_active = models.BooleanField(default=True, help_text="Indica si el elemento está activo")
    groups = models.ManyToManyField(Group, blank=True, help_text="Grupos que pueden ver este elemento")
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='children', 
        help_text="Elemento padre (para submenús)"
        )
    
    class Meta:
        ordering = ['menu', 'order', 'name']
        unique_together = ('menu', 'name')
        verbose_name = "Elemento de menú"
        verbose_name_plural = "Elementos de menú"
    
    def __str__(self):
        return f"{self.menu.name} - {self.name}"