# apps/accounting/models/tax.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

from apps.base.models.basemodel import BaseModel, CompleteModel
from apps.accounting.models.PUC import CuentaAuxiliar, CuentaDetalle
from apps.base.models.company import Company


class TaxType(BaseModel):
    """
    Tipos de impuestos en Colombia (IVA, INC, ReteFuente, etc.)
    """
    name = models.CharField(_('Nombre'), max_length=100)
    code = models.CharField(_('Código'), max_length=20, unique=True)
    description = models.TextField(_('Descripción'), blank=True)
    is_active = models.BooleanField(_('Activo'), default=True)
    
    class Meta:
        verbose_name = _('Tipo de Impuesto')
        verbose_name_plural = _('Tipos de Impuestos')
        ordering = ['name']
        
    def __str__(self):
        return self.name

class TaxRate(CompleteModel):
    """
    Tasas de impuestos específicas (por ejemplo, IVA 19%, 5%, etc.)
    """
    tax_type = models.ForeignKey(
        TaxType, 
        on_delete=models.PROTECT, 
        related_name='tax_rates',
        verbose_name=_('Tipo de Impuesto')
    )
    name = models.CharField(_('Nombre'), max_length=100)
    code = models.CharField(_('Código'), max_length=20)
    rate = models.DecimalField(
        _('Tasa'), 
        max_digits=7, 
        decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    description = models.TextField(_('Descripción'), blank=True)
    is_default = models.BooleanField(_('Es predeterminado'), default=False)
    valid_from = models.DateField(_('Válido desde'), null=True, blank=True)
    valid_to = models.DateField(_('Válido hasta'), null=True, blank=True)
    tax_account = models.ForeignKey(
        CuentaDetalle,
        on_delete=models.PROTECT,
        related_name='tax_rates',
        verbose_name=_('Cuenta Contable'),
        help_text=_('Cuenta contable para este impuesto')
    )
    
    class Meta:
        verbose_name = _('Tasa de Impuesto')
        verbose_name_plural = _('Tasas de Impuestos')
        ordering = ['tax_type', 'rate']
        unique_together = ['tax_type', 'code']
        
    def __str__(self):
        return f"{self.tax_type.name} {self.rate}% ({self.name})"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Asegurar que solo hay una tasa por defecto por tipo de impuesto
            self.__class__.objects.filter(
                tax_type=self.tax_type, 
                is_default=True
            ).update(is_default=False)
        super().save(*args, **kwargs)

class WithholdingTaxType(BaseModel):
    """
    Tipos de retención (ReteFuente, ReteIVA, ReteICA, etc.)
    """
    name = models.CharField(_('Nombre'), max_length=100)
    code = models.CharField(_('Código'), max_length=20, unique=True)
    description = models.TextField(_('Descripción'), blank=True)
    is_active = models.BooleanField(_('Activo'), default=True)
    
    class Meta:
        verbose_name = _('Tipo de Retención')
        verbose_name_plural = _('Tipos de Retención')
        ordering = ['name']
        
    def __str__(self):
        return self.name

class WithholdingTaxConcept(CompleteModel):
    """
    Conceptos de retención en la fuente
    """
    withholding_type = models.ForeignKey(
        WithholdingTaxType, 
        on_delete=models.PROTECT, 
        related_name='concepts',
        verbose_name=_('Tipo de Retención')
    )
    name = models.CharField(_('Nombre'), max_length=255)
    code = models.CharField(_('Código'), max_length=20)
    rate = models.DecimalField(
        _('Tasa'), 
        max_digits=7, 
        decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    min_base = models.DecimalField(
        _('Base mínima'), 
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    tax_account = models.ForeignKey(
        CuentaDetalle,
        on_delete=models.PROTECT,
        related_name='withholding_concepts',
        verbose_name=_('Cuenta Contable'),
        help_text=_('Cuenta contable para esta retención')
    )
    description = models.TextField(_('Descripción'), blank=True)
    valid_from = models.DateField(_('Válido desde'), null=True, blank=True)
    valid_to = models.DateField(_('Válido hasta'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Concepto de Retención')
        verbose_name_plural = _('Conceptos de Retención')
        ordering = ['withholding_type', 'code']
        unique_together = ['withholding_type', 'code']
        
    def __str__(self):
        return f"{self.withholding_type.name} - {self.name} ({self.rate}%)"

class CompanyTaxConfig(CompleteModel):
    """
    Configuración de impuestos por empresa
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='tax_configurations',
        verbose_name=_('Empresa')
    )
    tax_rate = models.ForeignKey(
        TaxRate,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='company_configs',
        verbose_name=_('Tasa de Impuesto')
    )
    withholding_concept = models.ForeignKey(
        WithholdingTaxConcept,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='company_configs',
        verbose_name=_('Concepto de Retención')
    )
    is_active = models.BooleanField(_('Activo'), default=True)
    custom_rate = models.DecimalField(
        _('Tasa Personalizada'), 
        max_digits=7, 
        decimal_places=4,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    custom_account = models.ForeignKey(
        CuentaAuxiliar,
        on_delete=models.PROTECT,
        related_name='tax_configurations',
        verbose_name=_('Cuenta Personalizada'),
        blank=True,
        null=True
    )
    applied_to = models.CharField(
        _('Aplicado a'),
        max_length=20,
        choices=[
            ('SALES', _('Ventas')),
            ('PURCHASES', _('Compras')),
            ('BOTH', _('Ambos'))
        ],
        default='BOTH'
    )
    
    class Meta:
        verbose_name = _('Configuración de Impuestos por Empresa')
        verbose_name_plural = _('Configuraciones de Impuestos por Empresa')
        unique_together = [
            ['company', 'tax_rate'],
            ['company', 'withholding_concept']
        ]
        
    def __str__(self):
        if self.tax_rate:
            return f"{self.company.name} - {self.tax_rate.name}"
        return f"{self.company.name} - {self.withholding_concept.name}"
    
    def clean(self):
        super().clean()
        if not self.tax_rate and not self.withholding_concept:
            raise models.ValidationError(
                _("Debe especificar una tasa de impuesto o un concepto de retención")
            )
        if self.tax_rate and self.withholding_concept:
            raise models.ValidationError(
                _("No puede especificar ambos: tasa de impuesto y concepto de retención")
            )