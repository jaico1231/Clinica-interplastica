# # apps/accounting/models.py
# from django.db import models
# from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
# from apps.base.models.basemodel import BaseModel
# from django.core.exceptions import ValidationError

# class AccountingPeriod(BaseModel):
#     name = models.CharField("Nombre del Periodo", max_length=100)
#     start_date = models.DateField("Fecha de Inicio", null=False)
#     end_date = models.DateField("Fecha de Cierre", null=False)
#     is_closed = models.BooleanField("Cerrado", default=False)
#     fiscal_year = models.PositiveIntegerField("Año Fiscal", null=False)

#     class Meta:
#         verbose_name = "Período Contable"
#         verbose_name_plural = "Períodos Contables"
#         constraints = [
#             models.UniqueConstraint(
#                 fields=['start_date', 'end_date'],
#                 name='unique_period_dates'
#             ),
#             models.CheckConstraint(
#                 check=models.Q(end_date__gt=models.F('start_date')),
#                 name='valid_date_range'
#             )
#         ]

#     def clean(self):
#         super().clean()
        
#         if self.start_date and self.fiscal_year:
#             if self.start_date.year != self.fiscal_year:
#                 raise ValidationError(
#                     {'fiscal_year': 'El año fiscal debe coincidir con el año de la fecha de inicio'}
#                 )
        
#         if self.start_date and self.end_date:
#             if self.end_date <= self.start_date:
#                 raise ValidationError(
#                     {'end_date': 'La fecha de cierre debe ser posterior a la fecha de inicio'}
#                 )

#     def save(self, *args, **kwargs):
#         self.full_clean()
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.name} ({self.start_date} - {self.end_date})"

# class Journal(BaseModel):
#     """
#     Diarios contables según requerimientos DIAN
#     Uso: Registro de comprobantes de contabilidad (Decreto 2420 de 2015)
#     """
#     JOURNAL_TYPES = (
#         ('INGRESO', 'Comprobantes de Ingreso'),
#         ('EGRESO', 'Comprobantes de Egreso'),
#         ('DIARIO', 'Comprobantes Diario'),
#         ('CAJA', 'Comprobantes de Caja'),
#         ('BANCOS', 'Comprobantes Bancarios'),
#     )
    
#     code = models.CharField("Código", max_length=10, unique=True)
#     name = models.CharField("Nombre", max_length=100)
#     type = models.CharField("Tipo", max_length=20, choices=JOURNAL_TYPES)
#     consecutive = models.PositiveIntegerField("Consecutivo Actual", default=1)
#     resolution_number = models.CharField(
#         "Resolución DIAN", 
#         max_length=50,
#         help_text="Número de resolución de numeración autorizada"
#     )

#     def get_next_consecutive(self):
#         self.consecutive += 1
#         self.save()
#         return f"{self.code}-{self.consecutive:08d}"

# class JournalEntry(BaseModel):
#     """
#     Asientos contables con validaciones legales colombianas
#     Uso: Cumplimiento de estructura de comprobantes contables (Art. 44 Ley 222/95)
#     """
#     entry = models.ForeignKey(
#         Journal,
#         on_delete=models.PROTECT,
#         verbose_name="Diario"
#     )
#     reference = models.CharField(
#         "Referencia", 
#         max_length=50,
#         unique=True,
#         editable=False  # Generado automáticamente
#     )
#     tax_validation = models.BooleanField(
#         "Validación Tributaria", 
#         default=False,
#         help_text="Cumple con estructura tributaria colombiana"
#     )

#     def save(self, *args, **kwargs):
#         if not self.reference:
#             self.reference = self.journal.get_next_consecutive()
#         super().save(*args, **kwargs)

# class JournalEntryLine(BaseModel):
#     """
#     Líneas de asiento con soporte para retenciones colombianas
#     Uso: Registro detallado con soporte para base gravable e impuestos
#     """
#     TAX_CODES = (
#         ('IVA19', 'IVA 19%'),
#         ('RETEICA', 'Retención ICA'),
#         ('RETEFUENTE', 'Retención en la Fuente'),
#         ('RETEIVA', 'Retención de IVA'),
#     )
    
#     tax_code = models.CharField(
#         "Código Impuesto", 
#         max_length=10, 
#         choices=TAX_CODES,
#         blank=True
#     )
#     tax_base = models.DecimalField(
#         "Base Gravable", 
#         max_digits=15, 
#         decimal_places=2, 
#         default=0
#     )
#     tax_amount = models.DecimalField(
#         "Valor Impuesto", 
#         max_digits=15, 
#         decimal_places=2, 
#         default=0
#     )
#     third_party = models.ForeignKey(
#         'Partner',
#         on_delete=models.PROTECT,
#         verbose_name="Tercero",
#         help_text="Identificación del tercero (NIT)"
#     )

#     class Meta:
#         constraints = [
#             models.CheckConstraint(
#                 check=models.Q(tax_code='') | models.Q(tax_amount__gt=0),
#                 name='tax_validation'
#             )
#         ]

# class ColombianTax(BaseModel):
#     """
#     Configuración de impuestos colombianos actualizados
#     Uso: Parametrización de tasas y conceptos según normativa DIAN
#     """
#     TAX_TYPE_CHOICES = (
#         ('IVA', 'Impuesto sobre las Ventas'),
#         ('RETE', 'Retenciones'),
#         ('ICA', 'Impuesto de Industria y Comercio'),
#         ('CREE', 'Impuesto sobre la Renta para la Equidad'),
#     )
    
#     code = models.CharField("Código DIAN", max_length=10)
#     name = models.CharField("Nombre", max_length=100)
#     rate = models.DecimalField(
#         "Tasa Vigente", 
#         max_digits=5, 
#         decimal_places=2,
#         validators=[MinValueValidator(0), MaxValueValidator(100)]
#     )
#     effective_date = models.DateField("Fecha Vigencia")
#     tax_account = models.ForeignKey(
#         'PUC',
#         on_delete=models.PROTECT,
#         related_name='tax_configurations'
#     )

# class Partner(BaseModel):
#     """
#     Terceros con validación de información tributaria colombiana
#     Uso: Registro de clientes/proveedores según Resolución 000013 DIAN
#     """
#     TAX_REGIMES = (
#         ('RST', 'Régimen Simple de Tributación'),
#         ('RNT', 'Régimen Ordinario'),
#         ('GRA', 'Gran Contribuyente'),
#     )
    
#     nit = models.CharField(
#         "NIT", 
#         max_length=15,
#         validators=[RegexValidator(r'^\d{9}-?\d$')]
#     )
#     tax_regime = models.CharField(
#         "Régimen Tributario", 
#         max_length=3, 
#         choices=TAX_REGIMES
#     )
#     ica_code = models.CharField(
#         "Código ICA", 
#         max_length=10, 
#         blank=True
#     )
#     dian_responsibilities = models.ManyToManyField(
#         'DianResponsibility',
#         verbose_name="Responsabilidades DIAN"
#     )

# class DianResponsibility(BaseModel):
#     """
#     Responsabilidades tributarias según Última Resolución DIAN
#     Uso: Validación automática de obligaciones tributarias
#     """
#     code = models.CharField("Código DIAN", max_length=10, unique=True)
#     description = models.TextField("Descripción")
#     effect_date = models.DateField("Fecha Efectiva")

# class Retention(BaseModel):
#     """
#     Modelo especializado para retenciones colombianas
#     Uso: Cálculo y registro de retenciones según tarifas DIAN
#     """
#     CONCEPT_CHOICES = (
#         ('01', 'Honorarios'),
#         ('02', 'Servicios'),
#         ('06', 'Arrendamientos'),
#     )
    
#     base_value = models.DecimalField("Base Retención", max_digits=15, decimal_places=2)
#     percentage = models.DecimalField("Porcentaje", max_digits=5, decimal_places=2)
#     concept_code = models.CharField("Código Concepto", max_length=2, choices=CONCEPT_CHOICES)
#     certificate_number = models.CharField("Certificado", max_length=20, unique=True)