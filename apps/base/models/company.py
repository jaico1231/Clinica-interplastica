# company.py
from django.db import models
from django.core.validators import RegexValidator
from apps.base.models.support import (
    AccountType, City, ComercialCompanyType, Country, DocType, 
    FiscalResponsibility, Periodicity, State, TaxRegime
)
from apps.base.models.basemodel import BaseModel, CompleteModel, SoftDeleteModel
from apps.base.models.users import User


def company_logo_path(instance, filename):
    """Genera la ruta para el logo de la empresa"""
    # Usar el pk en lugar de id que podría no estar disponible
    return f'companies/{instance.pk}/logo/{filename}'


class CompanyFiscalResponsibility(models.Model):
    """Relación entre Empresa y Responsabilidades fiscales"""
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    fiscal_responsibility = models.ForeignKey(FiscalResponsibility, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('company', 'fiscal_responsibility')
        verbose_name = 'Responsabilidad Fiscal de Empresa'
        verbose_name_plural = 'Responsabilidades Fiscales de Empresas'
    
    def __str__(self):
        return f"{self.company.name} - {self.fiscal_responsibility.name}"


class Company(BaseModel, SoftDeleteModel):
    """Modelo para la información de empresas"""
    # Información básica
    name = models.CharField(
        'Nombre de la Empresa',
        max_length=100,
        db_index=True  # Añadir índice para búsquedas por nombre
    )
    tax_id = models.CharField(
        'NIT',
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9-]*$',
                message='NIT debe contener solo números y guiones'
            )
        ]
    )
    address = models.CharField(
        'Dirección',
        max_length=200,
        null=True,
        blank=True
    )
    phone = models.CharField(
        'Teléfono',
        max_length=15,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Número de teléfono debe estar en formato: +999999999'
            )
        ]
    )
    email = models.EmailField(
        'Correo Electrónico',
        null=True,
        blank=True
    )

    # Información del representante legal
    legal_representative = models.CharField(
        'Representante Legal',
        max_length=100,
        null=True,
        blank=True
    )
    document_type = models.ForeignKey(
        DocType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Tipo de Documento',
        related_name='companies'  # Añadir related_name
    )
    representative_document = models.CharField(
        'Documento del Representante',
        max_length=20,
        null=True,
        blank=True
    )
    representative_position = models.CharField(
        'Cargo del Representante',
        max_length=100,
        null=True,
        blank=True
    )

    # Información de pagos
    payment_periodicity = models.ForeignKey(
        Periodicity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Periodicidad de Pago',
        related_name='companies'  # Añadir related_name
    )

    # Ubicación
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='País',
        related_name='companies'  # Añadir related_name
    )
    state = models.ForeignKey(
        State,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Departamento',
        related_name='companies'  # Añadir related_name
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Ciudad/Municipio',
        related_name='companies'  # Añadir related_name
    )

    # Información bancaria
    account_number = models.CharField(
        'Número de Cuenta',
        max_length=100,
        null=True,
        blank=True
    )
    bank_name = models.CharField(
        'Banco',
        max_length=100,
        null=True,
        blank=True
    )
    account_type = models.ForeignKey(
        AccountType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Tipo de Cuenta',
        related_name='companies'  # Añadir related_name
    )
    
    # Datos tributarios
    tax_regime = models.ForeignKey(
        TaxRegime,
        on_delete=models.SET_NULL,
        null=True,  # Cambiado de default=1 a null=True
        verbose_name='Régimen Tributario',
        related_name='companies'  # Añadir related_name
    )
    comercialcompany = models.ForeignKey(
        ComercialCompanyType,
        on_delete=models.SET_NULL,
        null=True,  # Cambiado de default=1 a null=True
        verbose_name='Tipo de Empresa',
        related_name='companies'  # Añadir related_name
    )
    fiscal_responsibilities = models.ManyToManyField(
        FiscalResponsibility,
        through='CompanyFiscalResponsibility',
        blank=True,
        verbose_name="Responsabilidades Fiscales",
        related_name='companies'  # Añadir related_name
    )
    
    # Logo
    logo = models.ImageField(
        'Logo de la Empresa',
        upload_to=company_logo_path,
        null=True,
        blank=True
    )

    # Estado
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['tax_id']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Si es una nueva instancia, guardar primero para tener el ID
        if not self.pk and self.logo:
            temp_logo = self.logo
            self.logo = None
            super().save(*args, **kwargs)
            self.logo = temp_logo
            
        super().save(*args, **kwargs)


class CompanyAccountingConfig(BaseModel):
    """
    Configuración contable específica para cada empresa
    """
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='accounting_config'
    )
    
    # Cuentas contables básicas
    cash_account = models.ForeignKey(
        'accounting.CuentaAuxiliar',
        on_delete=models.PROTECT,
        related_name='cash_configs',
        verbose_name='Cuenta de Caja'
    )
    accounts_receivable = models.ForeignKey(
        'accounting.CuentaAuxiliar',
        on_delete=models.PROTECT,
        related_name='receivable_configs',
        verbose_name='Cuentas por Cobrar'
    )
    sales_account = models.ForeignKey(
        'accounting.CuentaAuxiliar',
        on_delete=models.PROTECT,
        related_name='sales_configs',
        verbose_name='Cuenta de Ingresos'
    )
    iva_account = models.ForeignKey(
        'accounting.CuentaAuxiliar',
        on_delete=models.PROTECT,
        related_name='iva_configs',
        verbose_name='Cuenta de IVA'
    )
    ica_account = models.ForeignKey(
        'accounting.CuentaAuxiliar',
        on_delete=models.PROTECT,
        related_name='ica_configs',
        verbose_name='Cuenta de ICA',
        null=True,
        blank=True
    )
    withholding_tax_account = models.ForeignKey(
        'accounting.CuentaAuxiliar',
        on_delete=models.PROTECT,
        related_name='withholding_configs',
        verbose_name='Cuenta de Retención',
        null=True,
        blank=True
    )
    
    # Configuración de impuestos
    default_iva_rate = models.DecimalField(
        'Tasa IVA Predeterminada (%)',
        max_digits=5,
        decimal_places=2,
        default=19.00
    )
    apply_ica = models.BooleanField(
        'Aplica ICA',
        default=False
    )
    
    # Métodos de contabilidad
    use_fifo = models.BooleanField(
        'Usar FIFO para inventarios',
        default=True
    )
    automatic_accounting = models.BooleanField(
        'Contabilidad Automática',
        default=True,
        help_text='Generar asientos contables automáticamente'
    )
    
    class Meta:
        verbose_name = 'Configuración Contable'
        verbose_name_plural = 'Configuraciones Contables'
        indexes = [
            models.Index(fields=['company']),
        ]
        
    def __str__(self):
        # Corregido _str_ a __str__
        return f"Configuración contable de {self.company.name}"


class CompanyArea(CompleteModel):
    """
    Modelo para las áreas de la empresa
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='areas'
    )
    name = models.CharField(
        'Nombre del Área',
        max_length=100
    )
    description = models.TextField(
        'Descripción del Área',
        null=True,
        blank=True
    )
    default_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_manager_areas'
    )
    
    class Meta:
        verbose_name = 'Área de la Empresa'
        verbose_name_plural = 'Áreas de la Empresa'
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"