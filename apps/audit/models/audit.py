from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class AuditLog(models.Model):
    """
    Modelo para registrar todas las actividades de CRUD en las tablas de la aplicación
    """
    ACTION_CHOICES = (
        ('CREATE', _('Creación')),
        ('UPDATE', _('Modificación')),
        ('DELETE', _('Eliminación')),
        ('LOGIN', _('Inicio de sesión')),
        ('LOGOUT', _('Cierre de sesión')),
        ('VIEW', _('Visualización')),
        ('OTHER', _('Otra acción')),
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        verbose_name=_('Usuario'),
        related_name='audit_logs'
    )
    action = models.CharField(
        max_length=20, 
        choices=ACTION_CHOICES, 
        verbose_name=_('Acción')
    )
    timestamp = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Fecha y hora')
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True, 
        verbose_name=_('Dirección IP')
    )
    user_agent = models.TextField(
        null=True, 
        blank=True, 
        verbose_name=_('User Agent')
    )
    
    # Para referenciar cualquier modelo en la base de datos
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Tipo de contenido')
    )
    object_id = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        verbose_name=_('ID del objeto')
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Datos específicos
    table_name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        verbose_name=_('Nombre de tabla')
    )
    data_before = models.JSONField(
        null=True, 
        blank=True,
        verbose_name=_('Datos anteriores')
    )
    data_after = models.JSONField(
        null=True, 
        blank=True,
        verbose_name=_('Datos nuevos')
    )
    description = models.TextField(
        null=True, 
        blank=True,
        verbose_name=_('Descripción')
    )
    
    class Meta:
        verbose_name = _('Registro de auditoría')
        verbose_name_plural = _('Registros de auditoría')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['table_name']),
        ]
    
    def __str__(self):
        if self.user:
            return f"{self.get_action_display()} por {self.user.username} en {self.timestamp}"
        return f"{self.get_action_display()} en {self.timestamp}"