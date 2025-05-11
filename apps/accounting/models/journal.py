# apps/accounting/models/journal.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounting.models.tax import TaxRate, WithholdingTaxConcept
from apps.accounting.models.PUC import CuentaAuxiliar
from apps.base.models.basemodel import CompleteModel
from apps.base.models.company import Company
from apps.third_party.models.third_party import ThirdParty

class AccountingPeriod(CompleteModel):
    """
    Períodos contables según normativa colombiana
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='accounting_periods',
        verbose_name=_('Empresa')
    )
    name = models.CharField(_("Nombre del Periodo"), max_length=100)
    start_date = models.DateField(_("Fecha de Inicio"))
    end_date = models.DateField(_("Fecha de Cierre"))
    is_closed = models.BooleanField(_("Cerrado"), default=False)
    fiscal_year = models.PositiveIntegerField(_("Año Fiscal"))

    class Meta:
        verbose_name = _("Período Contable")
        verbose_name_plural = _("Períodos Contables")
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'start_date', 'end_date'],
                name='unique_company_period_dates'
            ),
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='valid_date_range'
            )
        ]
        ordering = ['-start_date']

    def clean(self):
        super().clean()
        
        if self.start_date and self.fiscal_year:
            if self.start_date.year != self.fiscal_year:
                raise ValidationError(
                    {'fiscal_year': _('El año fiscal debe coincidir con el año de la fecha de inicio')}
                )
        
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError(
                    {'end_date': _('La fecha de cierre debe ser posterior a la fecha de inicio')}
                )
            
            # Validar solapamiento con otros periodos
            overlapping = AccountingPeriod.objects.filter(
                company=self.company,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            )
            
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
                
            if overlapping.exists():
                raise ValidationError(
                    _('Este periodo se solapa con otros periodos existentes')
                )

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

class Journal(CompleteModel):
    """
    Diarios contables según requerimientos DIAN
    Uso: Registro de comprobantes de contabilidad (Decreto 2420 de 2015)
    """
    JOURNAL_TYPES = (
        ('INGRESO', _('Comprobantes de Ingreso')),
        ('EGRESO', _('Comprobantes de Egreso')),
        ('DIARIO', _('Comprobantes Diario')),
        ('VENTA', _('Facturas de Venta')),
        ('COMPRA', _('Facturas de Compra')),
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='journals',
        verbose_name=_('Empresa')
    )
    code = models.CharField(_("Código"), max_length=10)
    name = models.CharField(_("Nombre"), max_length=100)
    type = models.CharField(_("Tipo"), max_length=20, choices=JOURNAL_TYPES)
    consecutive = models.PositiveIntegerField(_("Consecutivo Actual"), default=1)
    prefix = models.CharField(_("Prefijo"), max_length=10, blank=True)
    resolution_number = models.CharField(
        _("Resolución DIAN"), 
        max_length=50,
        help_text=_("Número de resolución de numeración autorizada"),
        blank=True
    )
    resolution_date = models.DateField(
        _("Fecha de Resolución"),
        null=True,
        blank=True
    )
    valid_from = models.DateField(_("Válido Desde"), default=timezone.now)
    valid_to = models.DateField(_("Válido Hasta"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Diario Contable")
        verbose_name_plural = _("Diarios Contables")
        unique_together = [['company', 'code']]
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_next_consecutive(self):
        self.consecutive += 1
        self.save()
        return f"{self.prefix or self.code}-{self.consecutive:08d}"

class JournalEntry(CompleteModel):
    """
    Asientos contables con validaciones legales colombianas
    Uso: Cumplimiento de estructura de comprobantes contables (Art. 44 Ley 222/95)
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='journal_entries',
        verbose_name=_('Empresa')
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.PROTECT,
        related_name='entries',
        verbose_name=_("Diario")
    )
    accounting_period = models.ForeignKey(
        AccountingPeriod,
        on_delete=models.PROTECT,
        related_name='journal_entries',
        verbose_name=_("Período Contable")
    )
    reference = models.CharField(
        _("Referencia"), 
        max_length=50,
        help_text=_("Número de documento generado automáticamente")
    )
    date = models.DateField(_("Fecha"), default=timezone.now)
    description = models.TextField(_("Descripción"), blank=True)
    third_party = models.ForeignKey(
        ThirdParty,
        on_delete=models.PROTECT,
        related_name='journal_entries',
        verbose_name=_("Tercero")
    )
    is_posted = models.BooleanField(_("Contabilizado"), default=False)
    is_reconciled = models.BooleanField(_("Conciliado"), default=False)
    
    class Meta:
        verbose_name = _("Asiento Contable")
        verbose_name_plural = _("Asientos Contables")
        unique_together = [['company', 'journal', 'reference']]
        ordering = ['-date', 'reference']

    def __str__(self):
        return f"{self.reference} - {self.date}"

    def save(self, *args, **kwargs):
        # Generar referencia si es nuevo
        if not self.reference:
            self.reference = self.journal.get_next_consecutive()
            
        # Verificar que la fecha esté dentro del período contable
        if self.date and self.accounting_period:
            if self.date < self.accounting_period.start_date or self.date > self.accounting_period.end_date:
                raise ValidationError(
                    _("La fecha del asiento debe estar dentro del período contable seleccionado")
                )
                
        # Validar que el período no esté cerrado si se está modificando
        if self.accounting_period and self.accounting_period.is_closed:
            raise ValidationError(
                _("No se puede modificar un asiento en un período cerrado")
            )
            
        super().save(*args, **kwargs)
        
    def total_debits(self):
        return self.lines.filter(is_debit=True).aggregate(
            models.Sum('amount')
        )['amount__sum'] or 0
        
    def total_credits(self):
        return self.lines.filter(is_debit=False).aggregate(
            models.Sum('amount')
        )['amount__sum'] or 0
        
    def is_balanced(self):
        return abs(self.total_debits() - self.total_credits()) < 0.01

class JournalEntryLine(CompleteModel):
    """
    Líneas de asiento con soporte para impuestos colombianos
    """
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_("Asiento Contable")
    )
    account = models.ForeignKey(
        CuentaAuxiliar,
        on_delete=models.PROTECT,
        related_name='journal_entry_lines',
        verbose_name=_("Cuenta Contable")
    )
    description = models.CharField(_("Descripción"), max_length=255, blank=True)
    is_debit = models.BooleanField(_("Es Débito"), default=True)
    amount = models.DecimalField(
        _("Importe"), 
        max_digits=18, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    third_party = models.ForeignKey(
        ThirdParty,
        on_delete=models.PROTECT,
        related_name='journal_entry_lines',
        verbose_name=_("Tercero")
    )
    # Campos para impuestos
    tax_base = models.DecimalField(
        _("Base Gravable"), 
        max_digits=18, 
        decimal_places=2,
        default=0
    )
    tax_rate = models.ForeignKey(
        TaxRate,
        on_delete=models.PROTECT,
        related_name='journal_entry_lines',
        verbose_name=_("Tasa de Impuesto"),
        null=True,
        blank=True
    )
    withholding_concept = models.ForeignKey(
        WithholdingTaxConcept,
        on_delete=models.PROTECT,
        related_name='journal_entry_lines',
        verbose_name=_("Concepto de Retención"),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _("Línea de Asiento")
        verbose_name_plural = _("Líneas de Asiento")
        ordering = ['id']

    def __str__(self):
        debit_credit = _("DB") if self.is_debit else _("CR")
        return f"{self.journal_entry.reference} - {self.account.code} - {debit_credit} {self.amount}"
        
    def clean(self):
        super().clean()
        
        # Validar que la cuenta permita movimientos
        if self.account and not self.account.allows_movements:
            raise ValidationError(
                {'account': _('Esta cuenta no permite movimientos directos')}
            )
            
        # Validar coherencia de impuestos
        if self.tax_rate and self.withholding_concept:
            raise ValidationError(
                _("No puede especificar ambos: tasa de impuesto y concepto de retención")
            )
            
        if (self.tax_rate or self.withholding_concept) and self.tax_base <= 0:
            raise ValidationError(
                {'tax_base': _('La base gravable debe ser mayor que cero si se especifica un impuesto')}
            )