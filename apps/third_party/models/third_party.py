# apps/common/models/third_party.py
import os
from django.conf import settings
import importlib
from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator

from apps.base.models.support import AttachmentType, City, Country, DocType, State
from apps.base.models.basemodel import BaseModel,CompleteModel


def third_party_image_path(instance, filename):
    """Generate path for third party images"""
    doc_number = instance.document_number.replace(" ", "_").replace("-", "_")
    return os.path.join('img/third_party', doc_number, filename)

def third_party_document_path(instance, filename):
    """Generate path for third party documents"""
    doc_number = instance.third_party.document_number.replace(" ", "_").replace("-", "_")
    return os.path.join('docs/third_party', doc_number, filename)

class ThirdPartyType(CompleteModel):
    """Model for third party types"""
    name = models.CharField(
        "Nombre",
        max_length=150
    )
    code = models.CharField(
        "Sigla",
        max_length=10,
        unique=True
    )
    description = models.TextField(
        "Descripción",
        blank=True
    )
    is_active = models.BooleanField(
        "Activo",
        default=True
    )

    class Meta:
        verbose_name = 'Tipo de Tercero'
        verbose_name_plural = 'Tipos de Terceros'
        ordering = ['name']

    def __str__(self):
        return self.name

class ThirdParty(CompleteModel):
    """Model for third parties (customers, suppliers, employees, etc.)"""
    # Basic Information
    first_name = models.CharField(
        "Nombre",
        max_length=150
    )
    last_name = models.CharField(
        'Apellido',
        max_length=150,
        blank=True,
        null=True
    )
    company_name = models.CharField(
        'Razón Social',
        max_length=200,
        blank=True,
        null=True
    )
    trade_name = models.CharField(
        'Nombre Comercial',
        max_length=200,
        blank=True,
        null=True
    )
    document_type = models.ForeignKey(DocType, default=1,on_delete=models.PROTECT, related_name='third_parties', verbose_name='Tipo de Documento')
    document_number = models.CharField(
        "Documento",
        max_length=20,
        unique=True
    )
    address = models.CharField(
        "Dirección",
        max_length=200,
        blank=True
    )
    landline = models.CharField(
        "Teléfono Fijo",
        max_length=16,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Formato de teléfono inválido'
            )
        ]
    )
    mobile = models.CharField(
        "Teléfono Móvil",
        max_length=16,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Formato de teléfono inválido'
            )
        ]
    )
    email = models.EmailField(
        "Correo Electrónico",
        max_length=80,
        blank=True,
        null=True,
        unique=True
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name='third_parties',
        verbose_name='País',
        blank=True,
        null=True
    )
    state = models.ForeignKey(
        State,
        on_delete=models.PROTECT,
        related_name='third_parties',
        verbose_name='Departamento',
        blank=True,
        null=True
    )
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name='third_parties',
        verbose_name='Ciudad',
        blank=True,
        null=True
    )
    third_party_type = models.ForeignKey(
        ThirdPartyType,
        default=1,
        on_delete=models.PROTECT,
        related_name='third_parties',
        verbose_name='Tipo de Tercero'
    )
    advisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='advised_third_parties',
        verbose_name='Asesor',
        null=True,
        blank=True
    )    
    tax_regime = models.CharField(
        'Régimen Tributario',
        max_length=50,
        blank=True
    )
    tax_responsibility = models.CharField(
        'Responsabilidad Fiscal',
        max_length=50,
        blank=True
    )
    economic_activity = models.CharField(
        'Actividad Económica',
        max_length=100,
        blank=True
    )
    image = models.ImageField(
        'Imagen',
        upload_to=third_party_image_path,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Tercero"
        verbose_name_plural = 'Terceros'
        ordering = ['first_name', 'last_name']
        indexes = [
            models.Index(fields=['document_number']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f'{self.document_number} - {self.get_full_name()}'

    def get_absolute_url(self):
        return reverse('common:third-party-detail', kwargs={'pk': self.pk})

    def get_full_name(self):
        """Returns the full name of the third party"""
        if self.company_name:
            return self.company_name
        return f"{self.first_name} {self.last_name or ''}".strip()

class ThirdPartyAttachment(CompleteModel):
    """Model for third party attachments/documents"""
    third_party = models.ForeignKey(
        ThirdParty,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Tercero'
    )
    attachment_type = models.ForeignKey(
        AttachmentType,
        on_delete=models.PROTECT,
        related_name='third_party_attachments',
        verbose_name='Tipo de Anexo'
    )
    file = models.FileField(
        'Archivo',
        upload_to=third_party_document_path
    )
    description = models.TextField(
        'Descripción',
        blank=True
    )
    is_required = models.BooleanField(
        'Requerido',
        default=False
    )
    expiration_date = models.DateField(
        'Fecha de Vencimiento',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Anexo de Tercero"
        verbose_name_plural = 'Anexos de Terceros'
        ordering = ['third_party', 'attachment_type']

    def __str__(self):
        return f"{self.third_party} - {self.attachment_type}"