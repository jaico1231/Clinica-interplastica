# base/models/base.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class BaseModelManager(models.Manager):
    """Manager personalizado para incluir lógica base"""
    def get_queryset(self):
        return super().get_queryset().select_related(
            'created_by', 
            'modified_by'
        )

class SoftDeleteManager(models.Manager):
    """Manager para el borrado lógico"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class BaseModel(models.Model):
    """
    Modelo base con auditoría completa
    Uso: Heredar en todos los modelos que requieran seguimiento de cambios
    """
    created_at = models.DateTimeField(
        'Fecha de Creación', 
        auto_now_add=True,
        db_index=True  # Optimización para consultas frecuentes
    )
    modified_at = models.DateTimeField(
        'Fecha de Modificación', 
        auto_now=True,
        db_index=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Para formularios
        related_name='created_%(class)s_set',
        verbose_name='Creado por'
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_%(class)s_set',
        verbose_name='Modificado por'
    )

    objects = BaseModelManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']  # Orden default

    def save(self, *args, **kwargs):
        """Sobreescritura para auditoría automática"""
        # Asegúrate de que sea la ruta correcta
        from apps.base.models.utils import get_current_user
        user = get_current_user()
        
        if user and not self.pk:
            self.created_by = user
        if user:
            self.modified_by = user
        super().save(*args, **kwargs)

class SoftDeleteModel(models.Model):
    """
    Modelo para borrado lógico
    Uso: Heredar cuando se necesite desactivar registros en lugar de borrar
    """
    is_active = models.BooleanField(
        'Activo', 
        default=True,
        db_index=True  # Optimización para consultas
    )
    deleted_at = models.DateTimeField(
        'Fecha de Eliminación', 
        null=True, 
        blank=True
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_%(class)s_set',
        verbose_name='Eliminado por'
    )

    active_objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Override para borrado lógico"""
        from apps.base.models.utils import get_current_user
        
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deleted_by = get_current_user()
        self.save(update_fields=[
            'is_active', 
            'deleted_at', 
            'deleted_by'
        ])

class CompleteModel(BaseModel, SoftDeleteModel):
    """
    Modelo completo con todas las características base
    Uso: Heredar en la mayoría de modelos del sistema
    """
    class Meta(BaseModel.Meta, SoftDeleteModel.Meta):
        abstract = True
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
        ]