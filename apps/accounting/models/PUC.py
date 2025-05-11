# apps/accounting/models/puc.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.base.models.basemodel import BaseModel, CompleteModel
from apps.base.models.company import Company

class Naturaleza(BaseModel):
    """Naturaleza de las cuentas: Débito o Crédito"""
    name = models.CharField(_('Nombre'), max_length=50)
    code = models.CharField(_('Código'), max_length=1, unique=True)
    description = models.TextField(_('Descripción'), blank=True)

    class Meta:
        verbose_name = _('Naturaleza')
        verbose_name_plural = _('Naturalezas')
        ordering = ['code']

    def __str__(self):
        return self.name

class GrupoCuenta(BaseModel):
    """Grupos principales de cuentas (1-Activo, 2-Pasivo, etc.)"""
    code = models.CharField(_('Código'), max_length=4, unique=True)
    name = models.CharField(_('Nombre'), max_length=100)
    level = models.PositiveIntegerField(_('Nivel'))
    naturaleza = models.ForeignKey(
        Naturaleza, 
        on_delete=models.PROTECT, 
        related_name='grupos_cuenta',
        verbose_name=_('Naturaleza')
    )
    description = models.TextField(_('Descripción'), blank=True)

    class Meta:
        verbose_name = _('Grupo de Cuenta')
        verbose_name_plural = _('Grupos de Cuenta')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

class CuentaMayor(BaseModel):
    """Cuentas de mayor (nivel 2)"""
    code = models.CharField(_('Código'), max_length=6, unique=True)
    name = models.CharField(_('Nombre'), max_length=100)
    level = models.PositiveIntegerField(_('Nivel'))
    naturaleza = models.ForeignKey(
        Naturaleza, 
        on_delete=models.PROTECT, 
        related_name='cuentas_mayor',
        verbose_name=_('Naturaleza')
    )
    grupo = models.ForeignKey(
        GrupoCuenta,
        on_delete=models.PROTECT,
        related_name='cuentas_mayor',
        verbose_name=_('Grupo'),
        blank=True,
        null=True
    )
    description = models.TextField(_('Descripción'), blank=True)

    class Meta:
        verbose_name = _('Cuenta Mayor')
        verbose_name_plural = _('Cuentas Mayor')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Verificar coherencia con el grupo
        if self.code[:1] != self.grupo.code[:1]:
            raise ValueError(f"El código de la cuenta mayor debe iniciar con el código del grupo ({self.grupo.code[:1]})")
        super().save(*args, **kwargs)

class SubCuenta(BaseModel):
    """Subcuentas (nivel 3)"""
    code = models.CharField(_('Código'), max_length=10, unique=True)
    name = models.CharField(_('Nombre'), max_length=100)
    level = models.PositiveIntegerField(_('Nivel'))
    naturaleza = models.ForeignKey(
        Naturaleza, 
        on_delete=models.PROTECT, 
        related_name='sub_cuentas',
        verbose_name=_('Naturaleza')
    )
    cuenta_mayor = models.ForeignKey(
        CuentaMayor,
        on_delete=models.PROTECT,
        related_name='subcuentas',
        verbose_name=_('Cuenta Mayor'),
        blank=True,
        null=True
    )
    description = models.TextField(_('Descripción'), blank=True)
    
    class Meta:
        verbose_name = _('Subcuenta')
        verbose_name_plural = _('Subcuentas')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Verificar coherencia con la cuenta mayor
        if self.code[:2] != self.cuenta_mayor.code[:2]:
            raise ValueError(f"El código de la subcuenta debe iniciar con el código de la cuenta mayor ({self.cuenta_mayor.code[:2]})")
        super().save(*args, **kwargs)

class CuentaDetalle(CompleteModel):
    """Cuentas detalle (nivel 4)"""
    code = models.CharField(_('Código'), max_length=12, unique=True)
    name = models.CharField(_('Nombre'), max_length=100)
    level = models.PositiveIntegerField(_('Nivel'), default=4)
    naturaleza = models.ForeignKey(
        Naturaleza, 
        on_delete=models.PROTECT, 
        related_name='cuentas_detalle',
        verbose_name=_('Naturaleza')
    )
    subcuenta = models.ForeignKey(
        SubCuenta,
        on_delete=models.PROTECT,
        related_name='cuentas_detalle',
        verbose_name=_('Subcuenta'),
        blank=True,
        null=True
    )
    description = models.TextField(_('Descripción'), blank=True)
    is_tax_account = models.BooleanField(_('Es cuenta fiscal'), default=False)
    
    class Meta:
        verbose_name = _('Cuenta Detalle')
        verbose_name_plural = _('Cuentas Detalle')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Verificar coherencia con la subcuenta
        if self.code[:4] != self.subcuenta.code[:4]:
            raise ValueError(f"El código de la cuenta detalle debe iniciar con el código de la subcuenta ({self.subcuenta.code[:4]})")
        super().save(*args, **kwargs)

class CuentaAuxiliar(CompleteModel):
    """Cuentas auxiliares personalizadas (nivel 5)"""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='cuentas_auxiliares',
        verbose_name=_('Empresa'),
        blank=True,
        null=True
    )
    code = models.CharField(_('Código'), max_length=20)
    name = models.CharField(_('Nombre'), max_length=100)
    level = models.PositiveIntegerField(_('Nivel'), default=5)
    naturaleza = models.ForeignKey(
        Naturaleza, 
        on_delete=models.PROTECT, 
        related_name='cuentas_auxiliares',
        verbose_name=_('Naturaleza')
    )
    cuenta_detalle = models.ForeignKey(
        CuentaDetalle,
        on_delete=models.PROTECT,
        related_name='cuentas_auxiliares',
        verbose_name=_('Cuenta Detalle')
    )
    description = models.TextField(_('Descripción'), blank=True)
    is_tax_account = models.BooleanField(_('Es cuenta fiscal'), default=False)
    allows_movements = models.BooleanField(_('Permite movimientos'), default=True)
    
    class Meta:
        verbose_name = _('Cuenta Auxiliar')
        verbose_name_plural = _('Cuentas Auxiliares')
        ordering = ['code']
        unique_together = ['company', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Verificar coherencia con la cuenta detalle
        if self.code[:6] != self.cuenta_detalle.code[:6]:
            raise ValueError(f"El código de la cuenta auxiliar debe iniciar con el código de la cuenta detalle ({self.cuenta_detalle.code[:6]})")
        super().save(*args, **kwargs)