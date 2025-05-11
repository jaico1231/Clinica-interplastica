#support.py
# geografia.py
from django.db import models
from apps.base.models.basemodel import BaseModel, CompleteModel
from django.utils.translation import gettext_lazy as _
#Estado de la solicitud

class PermitType(BaseModel):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        verbose_name = 'Tipo de Permisos'
        verbose_name_plural = 'Tipos de Permisos'
        ordering = ['name']

    def __str__(self):
        return self.name


# AplicationStatus: para el estado de la solicitud (aprobada, rechazada, re agendado, finalizado, cancelado).
class AplicationStatus(BaseModel):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        verbose_name = 'Aplicación de Estado'
        verbose_name_plural = 'Aplicaciones de Estado'
        ordering = ['name']
    
    def __str__(self):
        return self.name

# RequestStatus: para el estado de la solicitud (abierto, en proceso, cerrado).
class RequestStatus(BaseModel):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Estado de Solicitud'
        verbose_name_plural = 'Estados de Solicitud'
        ordering = ['name']

    def __str__(self):
        return self.name

#DocType: Para clasificar tipos de documentos (por ejemplo, DNI, pasaporte, licencia de conducir).
class DocType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

#TransactionType: para claseificar el tipo de transaccion (Debito, Credito)
class TransactionType(BaseModel):
    name = models.CharField('Nombre', max_length=50)
    code = models.CharField('Código', max_length=10, unique=True)
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Tipo de Transacción'
        verbose_name_plural = 'Tipos de Transacciones'
        ordering = ['name']

    def __str__(self):
        return self.name

# AccountType: Para clasificar tipos de cuentas (por ejemplo, ahorros, corriente, inversión).
class AccountType(BaseModel):
    name = models.CharField('Nombre', max_length=50)
    code = models.CharField('Código', max_length=10, unique=True)
    is_active = models.BooleanField('Activo', default=True)

    class Meta: 
        verbose_name = 'Tipo de Cuenta'
        verbose_name_plural = 'Tipos de Cuenta'
        ordering = ['name']

    def __str__(self):
        return self.name

#Periodicity: clasificacion de la concurrencia de una actividad (Mensual, Trimestral...)
class Periodicity(BaseModel):
    name = models.CharField('Nombre', max_length=50)
    code = models.CharField('Código', max_length=10, unique=True)
    description = models.TextField('Descripción', blank=True, null=True)
    days = models.IntegerField('Dias')
    months = models.IntegerField('Meses')
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Tipo de Periodo'
        verbose_name_plural = 'Tipos de Periodo'
        ordering = ['name'] 

    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=60)
    iso_name = models.CharField(max_length=50)
    alfa2 = models.CharField(max_length=2)
    alfa3 = models.CharField(max_length=3)
    code = models.CharField(max_length=3)
    demonym = models.CharField(max_length=60, blank=True, null=True)
    def __str__ (self):
        return str(self.name)

    class Meta:
        verbose_name="Pais"
        verbose_name_plural = 'Pais'
        ordering = ['name']

class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=60)
    code = models.CharField(max_length=3)
    is_active = models.BooleanField(default=True)
    def __str__ (self):
        return str(self.name)

    class Meta:
        verbose_name="Departamento/Estado"
        verbose_name_plural = 'Departamento/Estado'
        ordering = ['name']

class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField("Municipio", max_length=255, blank=False, null=False)
    code = models.CharField(max_length=3,unique=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        verbose_name="Ciudad/Municipio"
        verbose_name_plural = "Ciudad/Municipios"
        ordering = ['name']

# Gender: Para clasificar géneros (por ejemplo, masculino, femenino, otro).
class Gender(models.Model):
    name = models.CharField(max_length=255, blank=False, null=False)
    def __str__(self):
        return str(self.name)
    class Meta:
        verbose_name="Genero"
        verbose_name_plural = "Generos"
        ordering = ['name']

#Tipo de Anexos
class AttachmentType(BaseModel):
    name = models.CharField('Nombre', max_length=100)
    code = models.CharField('Código', max_length=50, unique=True)
    description = models.TextField('Descripción', blank=True)
    allowed_extensions = models.CharField(
        'Extensiones Permitidas',
        max_length=200,
        help_text='Ej: .pdf,.doc,.docx'
    )
    max_file_size = models.PositiveIntegerField(
        'Tamaño Máximo (MB)',
        default=5
    )
    is_required = models.BooleanField('Es Requerido', default=False)
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Tipo de Archivo Adjunto'
        verbose_name_plural = 'Tipos de Archivos Adjuntos'

# PaymentMethod: Para clasificar métodos de pago (por ejemplo, tarjeta de crédito, transferencia bancaria, efectivo).
class PaymentMethod(BaseModel):
    name = models.CharField('Nombre', max_length=100)
    code = models.CharField('Código', max_length=50, unique=True)
    description = models.TextField('Descripción', blank=True)
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Metodo de Pago'
        verbose_name_plural = 'Metodos de Pago'
        ordering = ['name']
    
    def __str__(self):
        return self.name
#Soltero, Casado,...
class CivilStatus(BaseModel):
    name = models.CharField('Nombre', max_length=100)
    code = models.CharField('Código', max_length=50, unique=True)
    description = models.TextField('Descripción', blank=True)
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Estado Civil'
        verbose_name_plural = 'Estados Civiles'

    def __str__(self):
        return self.name

# A+, A-, B+, B-, AB+, AB-,...
class BloodType(models.Model):
    rh = models.CharField(max_length=2)
    abo = models.CharField(max_length=2)

    class Meta:
        verbose_name = 'Grupo Sanguineo'
        verbose_name_plural = 'Grupos Sanguineos'

    def __str__(self):
        return f'{self.rh}{self.abo}'

#Medio Tiempo, tiempo completo, Freelance
class JobType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Tipo de Trabajo'
        verbose_name_plural = 'Tipos de Trabajos'

    def __str__(self):
        return self.name

# ContractType: Para clasificar tipos de contratos (Indefinido, Termino Fijo...)
class ContractType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Tipo de Contrato'
        verbose_name_plural = 'Tipos de Contratos'

    def __str__(self):
        return self.name

# Suspencion, incapacidad...
class NoveltyType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Tipo de Permisos'
        verbose_name_plural = 'Tipos de Permisos'

    def __str__(self):
        return self.name

# Terminacion de contrato, renuncia
class RetirementType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Tipo de Retiro'
        verbose_name_plural = 'Tipos de Retiros'

    def __str__(self):
        return self.name

class SeveranceWithdawalType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Tipo de Retiro de Cesantias'
        verbose_name_plural = 'Tipo de Retiro de Cesantias'

    def __str__(self):
        return self.name

# HousingType: Para clasificar tipos de vivienda (por ejemplo, casa, apartamento, loft).
class HousingType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Tipo de Vivienda'
        verbose_name_plural = 'Tipos de Viviendas'

    def __str__(self):
        return self.name

class EPS(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'EPS'
        verbose_name_plural = 'EPS'

    def __str__(self):
        return self.name

class ARL(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'ARL'
        verbose_name_plural = 'ARL'

    def __str__(self):
        return self.name

class PensionFound(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Fondo de Pensiones'
        verbose_name_plural = 'Fondos de Pensiones'

    def __str__(self):
        return self.name

#ProductType Para clasificar los eventos del sistema ejemple: Ingreso, Salida, Cambio de Departamento, Cambio de Puesto, etc.
class ProductType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Tipo de Producto'
        verbose_name_plural = 'Tipos de Productos'
        ordering = ['name']

# TaskType: Para clasificar tipos de tareas (por ejemplo, llamada, reunión, correo electrónico).
class TaskType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# ServiceType: Para clasificar tipos de servicios (por ejemplo, consultoría, soporte, mantenimiento).

class ServiceType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# InvoiceStatus: Para clasificar estados de facturas (por ejemplo, pendiente, pagada, vencida).

class InvoiceStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# Priority: Para clasificar prioridades (por ejemplo, baja, media, alta).
class Priority(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# IndustryType: Para clasificar tipos de industrias (por ejemplo, tecnología, salud, finanzas).
class IndustryType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# CommunicationType: Para clasificar tipos de comunicación (por ejemplo, correo electrónico, teléfono, chat).

class CommunicationType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# TaxRegime: Para clasificar regímenes fiscales (por ejemplo, régimen simplificado, régimen común).
class TaxRegime(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# Tipos de sociedades comerciales
class ComercialCompanyType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# TaxRegime: Para clasificar regímenes fiscales (por ejemplo, simplificado, ordinario).
class FiscalResponsibility(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

#ThemeType: Para clasificar tipos de tema visual del proyecto
# ('light', _('Claro')),
# ('dark', _('Oscuro')),
# ('system', _('Sistema')),
class ThemeType(BaseModel):
    """Temas de interfaz para el usuario"""
    name = models.CharField(_('Nombre'), max_length=50)
    code = models.CharField(_('Código'), max_length=20, unique=True)
    description = models.TextField(_('Descripción'), blank=True)
    css_class = models.CharField(_('Clase CSS'), max_length=50, blank=True)
    is_active = models.BooleanField(_('Activo'), default=True)
    is_default = models.BooleanField(_('Por defecto'), default=False)

    class Meta:
        verbose_name = _('Tema')
        verbose_name_plural = _('Temas')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            # Asegurarse de que solo haya un tema por defecto
            ThemeType.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class QuestionType(CompleteModel):
    """Model to define different types of questions"""
    name = models.CharField(_("Type Name"), max_length=50, unique=True)
    description = models.TextField(_("Description"), blank=True)
    
    # Define built-in question types
    TEXT = 'TEXT'
    TEXT_AREA = 'TEXT_AREA'
    SINGLE_CHOICE = 'SINGLE_CHOICE'
    MULTIPLE_CHOICE = 'MULTIPLE_CHOICE'
    RATING = 'RATING'
    DATE = 'DATE'
    NUMBER = 'NUMBER'
    YES_NO = 'YES_NO'
    HIERARCHY = 'HIERARCHY'  # Added hierarchical question type
    
    class Meta(CompleteModel.Meta):
        verbose_name = _('Question Type')
        verbose_name_plural = _('Question Types')
    
    def __str__(self):
        return self.name
