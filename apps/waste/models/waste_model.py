from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator

from apps.base.models.basemodel import BaseModel
from apps.base.models.company import CompanyArea


class WasteManager(BaseModel):
    """Waste management companies that receive waste"""
    """empresas de gestión de residuos que reciben residuos"""
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=20, unique=True)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    environmental_license = models.CharField(max_length=100, blank=True, null=True)
    license_date = models.DateField(blank=True, null=True)
    license_expiry_date = models.DateField(blank=True, null=True)  # Fecha de vencimiento de la licencia
    contact_person = models.CharField(max_length=200, blank=True, null=True)  # Persona de contacto
    contact_phone = models.CharField(max_length=50, blank=True, null=True)  # Teléfono de contacto
    services_offered = models.TextField(blank=True, null=True)  # Servicios ofrecidos
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Waste Manager"
        verbose_name_plural = "Waste Managers"
        ordering = ['name']
    
    @property
    def license_status(self):
        """Verificar el estado de la licencia"""
        if not self.environmental_license:
            return "Sin licencia"
        if not self.license_expiry_date:
            return "Sin fecha de vencimiento"
        
        today = timezone.now().date()
        days_to_expiry = (self.license_expiry_date - today).days
        
        if days_to_expiry < 0:
            return "Vencida"
        elif days_to_expiry <= 30:
            return f"Por vencer ({days_to_expiry} días)"
        else:
            return "Vigente"


class WasteType(BaseModel):
    """Categories of managed waste"""
    """tipos de residuos"""
    CATEGORIES = [
        ('ORDINARY', 'Ordinary'),
        ('RECYCLABLE', 'Recyclable'),
        ('HAZARDOUS', 'Hazardous'),
        ('SPECIAL', 'Special'),
        ('BIODEGRADABLE', 'Biodegradable'),  # Añadido para residuos orgánicos/compostables
        ('ELECTRONIC', 'Electronic Waste'),  # Añadido para residuos electrónicos
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    description = models.TextField(blank=True, null=True)
    identification_color = models.CharField(max_length=20, blank=True, null=True)
    requires_special_treatment = models.BooleanField(default=False)
    handling_instructions = models.TextField(blank=True, null=True)
    storage_requirements = models.TextField(blank=True, null=True)  # Requisitos de almacenamiento
    safety_measures = models.TextField(blank=True, null=True)  # Medidas de seguridad
    legal_classification = models.CharField(max_length=100, blank=True, null=True)  # Clasificación legal si aplica
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    class Meta:
        verbose_name = "Waste Type"
        verbose_name_plural = "Waste Types"
        ordering = ['category', 'name']
        
    @property
    def is_hazardous(self):
        return self.category in ['HAZARDOUS', 'SPECIAL']

    @property 
    def treatment_options(self):
        """Retorna las opciones de tratamiento recomendadas según el tipo de residuo"""
        if self.category == 'RECYCLABLE':
            return ['RECYCLING']
        elif self.category == 'BIODEGRADABLE':
            return ['COMPOSTING']
        elif self.category == 'HAZARDOUS':
            return ['INCINERATION', 'SECURITY_CELL', 'ENCAPSULATION']
        elif self.category == 'ELECTRONIC':
            return ['RECYCLING', 'SPECIAL_TREATMENT']
        else:
            return ['LANDFILL']


class WasteRecord(BaseModel):
    """Daily record of waste generation"""
    """registro diario de residuos"""
    UNITS = [
        ('KG', 'Kilograms'),
        ('TON', 'Tons'),
        ('M3', 'Cubic meters'),
        ('L', 'Liters'),
        ('UN', 'Units'),
    ]
    
    record_date = models.DateField(default=timezone.now)  # Cambiado de auto_now_add para permitir edición
    area = models.ForeignKey(CompanyArea, on_delete=models.CASCADE, null=True, blank=True)  # Añadido campo área
    waste_type = models.ForeignKey(WasteType, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=5, choices=UNITS, default='KG')
    container_type = models.CharField(max_length=100, blank=True, null=True)  # Tipo de contenedor
    responsible = models.CharField(max_length=200, blank=True, null=True)  # Responsable del registro
    storage_location = models.CharField(max_length=200, blank=True, null=True)  # Ubicación de almacenamiento
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.record_date} - {self.waste_type.name} ({self.quantity} {self.get_unit_display()})"
    
    class Meta:
        verbose_name = "Waste Record"
        verbose_name_plural = "Waste Records"
        ordering = ['-record_date', 'area', 'waste_type']
        
    @property
    def weight_kg(self):
        """Convert all measurements to KG for calculations"""
        """Convierte todas las medidas a KG para cálculos"""
        if self.unit == 'KG':
            return self.quantity
        elif self.unit == 'TON':
            return self.quantity * 1000
        elif self.unit == 'L' and self.waste_type.category in ['HAZARDOUS', 'SPECIAL']:
            # Aproximación: densidad promedio de residuos líquidos peligrosos
            # Esto debería ajustarse según el tipo específico
            return self.quantity * 0.9
        else:
            return self.quantity  # Para otros tipos, se requiere conversión específica


class WasteDestination(BaseModel):
    """Record of the final destination of waste"""
    """destino final de residuos"""
    TREATMENT_METHODS = [
        ('RECYCLING', 'Recycling'),
        ('COMPOSTING', 'Composting'),
        ('INCINERATION', 'Incineration'),
        ('LANDFILL', 'Landfill'),
        ('SECURITY_CELL', 'Security Cell'),
        ('ENCAPSULATION', 'Encapsulation'),
        ('SPECIAL_TREATMENT', 'Special Treatment'),  # Para tratamientos especiales
        ('REUSE', 'Reuse/Reconditioning'),  # Para reutilización
        ('OTHER', 'Other (Specify)'),
    ]
    
    STATUSES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('TREATED', 'Treated'),
        ('CERTIFIED', 'Certificate Issued'),
        ('RETURNED', 'Returned/Rejected'),  # Para envíos rechazados
    ]
    
    departure_date = models.DateField()
    area = models.ForeignKey(CompanyArea, on_delete=models.CASCADE, null=True, blank=True)  # Añadido campo área
    manager = models.ForeignKey(WasteManager, on_delete=models.CASCADE)
    waste_type = models.ForeignKey(WasteType, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=5, choices=WasteRecord.UNITS, default='KG')
    treatment_method = models.CharField(max_length=20, choices=TREATMENT_METHODS)
    other_method = models.CharField(max_length=100, blank=True, null=True)
    manifest_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='SCHEDULED')
    carrier = models.CharField(max_length=200, blank=True, null=True)
    vehicle_plate = models.CharField(max_length=20, blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    treatment_date = models.DateField(blank=True, null=True)
    certificate_number = models.CharField(max_length=50, blank=True, null=True)
    certificate_date = models.DateField(blank=True, null=True)  # Fecha del certificado
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)  # Razón de rechazo si aplica
    responsible = models.CharField(max_length=200, blank=True, null=True)  # Responsable del envío
    cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # Costo del tratamiento
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.departure_date} - {self.waste_type.name} to {self.manager.name}"
    
    class Meta:
        verbose_name = "Waste Destination"
        verbose_name_plural = "Waste Destinations"
        ordering = ['-departure_date', 'waste_type']  # Corregido: eliminado 'area'
        
    def is_complete(self):
        """Verifies if the process is completed with certificate"""
        return self.status == 'CERTIFIED' and self.certificate_number and self.certificate_file
    
    @property
    def weight_kg(self):
        """Convert all measurements to KG for calculations"""
        if self.unit == 'KG':
            return self.quantity
        elif self.unit == 'TON':
            return self.quantity * 1000
        elif self.unit == 'L' and self.waste_type.category in ['HAZARDOUS', 'SPECIAL']:
            # Aproximación: densidad promedio de residuos líquidos peligrosos
            return self.quantity * 0.9
        else:
            return self.quantity
    
    @property
    def duration_days(self):
        """Calculate duration of the waste management process"""
        if not self.treatment_date or not self.departure_date:
            return None
        return (self.treatment_date - self.departure_date).days
    
    def get_quantity_display(self):
        """Returns a formatted string with quantity and unit"""
        return f"{self.quantity} {self.get_unit_display()}"


def get_waste_media_path(instance, filename):
    """Function to get the upload path for waste media files"""
    """Función para obtener la ruta de carga de archivos multimedia de residuos"""
    today = timezone.now().strftime('%Y/%m/%d')
    if instance.record:
        return f'waste/records/{today}/{instance.record.id}/{filename}'
    elif instance.destination:
        return f'waste/destinations/{today}/{instance.destination.id}/{filename}'
    else:
        return f'waste/other/{today}/{filename}'


class WasteMediaFile(BaseModel):
    """Attached files to waste records (photos, documents, etc.)"""
    """archivos adjuntos a los registros de residuos (fotos, documentos, etc.)"""
    
    FILE_TYPES = [
        ('IMAGE', 'Image'),
        ('DOCUMENT', 'Document'),
        ('VIDEO', 'Video'),
        ('CERTIFICATE', 'Certificate'),
        ('OTHER', 'Other'),
    ]
    
    record = models.ForeignKey(WasteRecord, on_delete=models.CASCADE, related_name='files', blank=True, null=True)
    destination = models.ForeignKey(WasteDestination, on_delete=models.CASCADE, related_name='files', blank=True, null=True)
    file = models.FileField(upload_to=get_waste_media_path)
    filename = models.CharField(max_length=255, blank=True, null=True)  # Nombre original del archivo
    file_type = models.CharField(max_length=50)
    media_type = models.CharField(max_length=20, choices=FILE_TYPES, default='OTHER')  # Tipo de archivo multimedia
    description = models.CharField(max_length=200, blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)  # Fecha de carga
    
    def __str__(self):
        record_or_dest = self.record or self.destination
        if record_or_dest:
            return f"{self.get_media_type_display()} for {record_or_dest}"
        return f"{self.get_media_type_display()} - {self.filename or self.id}"
    
    class Meta:
        verbose_name = "Waste File"
        verbose_name_plural = "Waste Files"
        ordering = ['-upload_date']
    
    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = self.file.name
        super().save(*args, **kwargs)


class WasteIndicator(BaseModel):
    """Waste management indicators and goals"""
    """indicadores y metas de gestión de residuos"""
    
    INDICATOR_TYPES = [
        ('GENERATION', 'Waste Generation'),
        ('RECYCLING', 'Recycling Rate'),
        ('REDUCTION', 'Waste Reduction'),
        ('HAZARDOUS', 'Hazardous Waste Management'),
        ('COST', 'Waste Management Cost'),
    ]
    
    PERIODS = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    ]
    
    name = models.CharField(max_length=200)
    indicator_type = models.CharField(max_length=20, choices=INDICATOR_TYPES)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=50)  # Unidad de medida del indicador
    formula = models.TextField(blank=True, null=True)  # Fórmula de cálculo
    target_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Valor meta
    measurement_period = models.CharField(max_length=20, choices=PERIODS, default='MONTHLY')
    baseline_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Valor de referencia
    baseline_date = models.DateField(blank=True, null=True)  # Fecha de referencia
    is_active = models.BooleanField(default=True)
    waste_type = models.ForeignKey(WasteType, on_delete=models.SET_NULL, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_indicator_type_display()})"
    
    class Meta:
        verbose_name = "Waste Indicator"
        verbose_name_plural = "Waste Indicators"
        ordering = ['indicator_type', 'name']