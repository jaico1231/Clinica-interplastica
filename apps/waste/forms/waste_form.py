from django import forms
from django.utils.translation import gettext as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

from apps.waste.models.waste_model import WasteRecord, WasteType, WasteDestination, WasteManager, WasteMediaFile
from apps.base.models.company import CompanyArea
from apps.waste.widgets.multiple import MultipleFileInput

class WasteManagerForm(forms.ModelForm):
    """
    Formulario para la gestión de empresas gestoras de residuos.
    """
    
    class Meta:
        model = WasteManager
        fields = [
            'name', 'tax_id', 'address', 'city', 'phone', 
            'email', 'website', 'environmental_license', 
            'license_date', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'required': True, 'placeholder': _('Nombre de la empresa')}
            ),
            'tax_id': forms.TextInput(
                attrs={'class': 'form-control', 'required': True, 'placeholder': _('NIT / Identificación fiscal')}
            ),
            'address': forms.TextInput(
                attrs={'class': 'form-control', 'required': True, 'placeholder': _('Dirección')}
            ),
            'city': forms.TextInput(
                attrs={'class': 'form-control', 'required': True, 'placeholder': _('Ciudad')}
            ),
            'phone': forms.TextInput(
                attrs={'class': 'form-control', 'required': True, 'placeholder': _('Teléfono')}
            ),
            'email': forms.EmailInput(
                attrs={'class': 'form-control', 'required': True, 'placeholder': _('Correo electrónico')}
            ),
            'website': forms.URLInput(
                attrs={'class': 'form-control', 'placeholder': _('Sitio web (ej. https://www.empresa.com)')}
            ),
            'environmental_license': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': _('Número de licencia ambiental')}
            ),
            'license_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date', 'placeholder': _('Fecha de expedición de licencia')}
            ),
            'is_active': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar etiquetas personalizadas
        self.fields['name'].label = _('Nombre')
        self.fields['tax_id'].label = _('NIT / Identificación fiscal')
        self.fields['address'].label = _('Dirección')
        self.fields['city'].label = _('Ciudad')
        self.fields['phone'].label = _('Teléfono')
        self.fields['email'].label = _('Correo electrónico')
        self.fields['website'].label = _('Sitio web')
        self.fields['environmental_license'].label = _('Licencia ambiental')
        self.fields['license_date'].label = _('Fecha de licencia')
        self.fields['is_active'].label = _('¿Activo?')
        
    def clean_tax_id(self):
        """Validar que el NIT sea único"""
        tax_id = self.cleaned_data.get('tax_id')
        instance = getattr(self, 'instance', None)
        
        # Verificar que no exista otro gestor con el mismo NIT (excluyendo esta instancia)
        if tax_id and instance and instance.pk:
            if WasteManager.objects.filter(tax_id=tax_id).exclude(pk=instance.pk).exists():
                raise forms.ValidationError(_('Ya existe un gestor registrado con este NIT.'))
        elif tax_id and WasteManager.objects.filter(tax_id=tax_id).exists():
            raise forms.ValidationError(_('Ya existe un gestor registrado con este NIT.'))
            
        return tax_id
    
    def clean_license_date(self):
        """Validar que la fecha de licencia sea proporcionada si hay número de licencia"""
        license_date = self.cleaned_data.get('license_date')
        environmental_license = self.cleaned_data.get('environmental_license')
        
        if environmental_license and not license_date:
            raise forms.ValidationError(_('Si ingresa un número de licencia, debe proporcionar la fecha de expedición.'))
            
        return license_date


class WasteRecordForm(forms.ModelForm):
    """
    Formulario para crear y editar registros de residuos
    """
    # Campo de fecha con validación de no fecha futura
    record_date_hidden = forms.DateField(
        label=_('Fecha de Registro'),
        required=True,
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'class': 'form-control',
                'type': 'date',
                'max': timezone.now().strftime('%Y-%m-%d')
            }
        )
    )
    
    # Campo para archivos adjuntos
    media_files = forms.FileField(
        label=_('Archivos adjuntos'),
        required=False,
        widget=MultipleFileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = WasteRecord
        fields = [
            'area', 
            'waste_type', 
            'quantity', 
            'unit', 
            'container_type',
            'responsible',
            'storage_location',
            'notes'
        ]
        widgets = {
            'area': forms.Select(attrs={'class': 'form-control select2'}),
            'waste_type': forms.Select(attrs={'class': 'form-control select2'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'container_type': forms.TextInput(attrs={'class': 'form-control'}),
            'responsible': forms.TextInput(attrs={'class': 'form-control'}),
            'storage_location': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'area': _('Área'),
            'waste_type': _('Tipo de residuo'),
            'quantity': _('Cantidad'),
            'unit': _('Unidad de medida'),
            'container_type': _('Tipo de contenedor'),
            'responsible': _('Responsable'),
            'storage_location': _('Ubicación de almacenamiento'),
            'notes': _('Notas adicionales'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campos obligatorios
        self.fields['record_date_hidden'].required = True
        self.fields['area'].required = True
        self.fields['waste_type'].required = True
        self.fields['quantity'].required = True
        
        # Configurar campos opcionales
        self.fields['container_type'].required = False
        self.fields['responsible'].required = False
        self.fields['storage_location'].required = False
        self.fields['notes'].required = False
        
        # Inicializar el campo de fecha con el valor del modelo
        if self.instance and self.instance.pk:
            self.fields['record_date_hidden'].initial = self.instance.record_date
        else:
            self.fields['record_date_hidden'].initial = timezone.now().date()
        
        # Filtrar solo áreas activas
        self.fields['area'].queryset = CompanyArea.objects.filter(is_active=True).order_by('name')
        
        # Filtrar solo tipos de residuos activos
        self.fields['waste_type'].queryset = WasteType.objects.filter(is_active=True).order_by('category', 'name')
        
        # Agregar clases de Bootstrap para validación
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['required'] = 'required'
                if field.label:
                    field.label = f"{field.label} *"
                    
        # Establecer fecha máxima como hoy
        self.fields['record_date_hidden'].widget.attrs['max'] = timezone.now().strftime('%Y-%m-%d')
    
    def clean_record_date_hidden(self):
        """Validar que la fecha no sea futura"""
        date = self.cleaned_data.get('record_date_hidden')
        if date and date > timezone.now().date():
            raise ValidationError(_('La fecha no puede ser futura'))
        return date
    
    def clean_quantity(self):
        """Validar que la cantidad sea positiva"""
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError(_('La cantidad debe ser mayor que cero'))
        return quantity
    
    def clean_media_files(self):
        """Validar archivos adjuntos"""
        media_files = self.files.getlist('media_files')
        if media_files:
            for file in media_files:
                # Validar tamaño máximo de archivo
                if file.size > settings.MAX_UPLOAD_SIZE:
                    max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
                    raise ValidationError(_(f'El archivo {file.name} excede el tamaño máximo permitido de {max_size_mb}MB'))
                
                # Validar extensiones permitidas
                ext = file.name.split('.')[-1].lower()
                if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
                    raise ValidationError(_(f'La extensión del archivo {file.name} no está permitida. Extensiones permitidas: {", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)}'))
        return media_files
    
    def save(self, commit=True):
        """Guardar el registro y los archivos adjuntos"""
        instance = super().save(commit=False)
        
        # Establecer la fecha de registro desde el campo oculto
        instance.record_date = self.cleaned_data.get('record_date_hidden')
        
        # Actualizar campos de auditoría si es necesario
        if not instance.pk:
            instance.created_at = timezone.now()
        instance.updated_at = timezone.now()
        
        if commit:
            instance.save()
            
            # Guardar archivos adjuntos
            media_files = self.files.getlist('media_files')
            for file in media_files:
                # Guardar el archivo
                WasteMediaFile.objects.create(
                    waste_record=instance,
                    file=file,
                    filename=file.name,
                    file_type=file.name.split('.')[-1].lower()
                )
                
        return instance



class WasteDestinationForm(forms.ModelForm):
    """
    Formulario para la gestión de destinos finales de residuos.
    Incluye validaciones específicas y configuración de widgets estándar de Django.
    """
    
    class Meta:
        model = WasteDestination
        fields = [
            'departure_date', 'manager', 'waste_type', 'quantity', 'unit',
            'treatment_method', 'other_method', 'manifest_number', 'status',
            'carrier', 'vehicle_plate', 'delivery_date', 'treatment_date',
            'certificate_number', 'certificate_file', 'notes'
        ]
        widgets = {
            'departure_date': forms.DateInput(
                attrs={'class': 'form-control', 'required': True, 'type': 'date'}
            ),
            'manager': forms.Select(
                attrs={'class': 'form-control select2', 'required': True}
            ),
            'waste_type': forms.Select(
                attrs={'class': 'form-control select2', 'required': True}
            ),
            'quantity': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'required': True}
            ),
            'unit': forms.Select(
                attrs={'class': 'form-control', 'required': True}
            ),
            'treatment_method': forms.Select(
                attrs={'class': 'form-control', 'required': True}
            ),
            'other_method': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': _('Especifique el método de tratamiento')}
            ),
            'manifest_number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': _('Número de manifiesto de transporte')}
            ),
            'status': forms.Select(
                attrs={'class': 'form-control', 'required': True}
            ),
            'carrier': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': _('Nombre de la empresa transportadora')}
            ),
            'vehicle_plate': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': _('Placa del vehículo')}
            ),
            'delivery_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'treatment_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'certificate_number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': _('Número del certificado de disposición')}
            ),
            'certificate_file': forms.FileInput(
                attrs={'class': 'form-control-file'}
            ),
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Notas adicionales o comentarios')}
            ),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar gestores activos solamente
        self.fields['manager'].queryset = WasteManager.objects.filter(is_active=True).order_by('name')
        
        # Filtrar tipos de residuos activos solamente
        self.fields['waste_type'].queryset = WasteType.objects.filter(is_active=True).order_by('name')
        
        # Configurar etiquetas personalizadas
        self.fields['departure_date'].label = _('Fecha de Salida')
        self.fields['manager'].label = _('Gestor de Residuos')
        self.fields['waste_type'].label = _('Tipo de Residuo')
        self.fields['quantity'].label = _('Cantidad')
        self.fields['unit'].label = _('Unidad')
        self.fields['treatment_method'].label = _('Método de Tratamiento')
        self.fields['other_method'].label = _('Otro Método (Si aplica)')
        self.fields['manifest_number'].label = _('Número de Manifiesto')
        self.fields['status'].label = _('Estado')
        self.fields['carrier'].label = _('Transportador')
        self.fields['vehicle_plate'].label = _('Placa del Vehículo')
        self.fields['delivery_date'].label = _('Fecha de Entrega')
        self.fields['treatment_date'].label = _('Fecha de Tratamiento')
        self.fields['certificate_number'].label = _('Número de Certificado')
        self.fields['certificate_file'].label = _('Archivo de Certificado')
        self.fields['notes'].label = _('Notas Adicionales')
        
        # Establecer campos requeridos según el estado
        instance = kwargs.get('instance')
        if instance and instance.status == 'CERTIFIED':
            self.fields['certificate_number'].required = True
            self.fields['certificate_file'].required = True
        
        # Si tiene un área definida, establecer como campo oculto o información adicional
        if 'area' in self.fields:
            self.fields['area'].widget = forms.HiddenInput()
    
    def clean(self):
        """
        Validaciones adicionales para el formulario:
        - Si el método de tratamiento es 'OTHER', el campo 'other_method' es obligatorio
        - Si el estado es 'IN_TRANSIT' o superior, se requieren datos de transporte
        - Si el estado es 'DELIVERED' o superior, se requiere fecha de entrega
        - Si el estado es 'TREATED' o superior, se requiere fecha de tratamiento
        - Si el estado es 'CERTIFIED', se requieren número y archivo de certificado
        """
        cleaned_data = super().clean()
        treatment_method = cleaned_data.get('treatment_method')
        other_method = cleaned_data.get('other_method')
        status = cleaned_data.get('status')
        carrier = cleaned_data.get('carrier')
        vehicle_plate = cleaned_data.get('vehicle_plate')
        delivery_date = cleaned_data.get('delivery_date')
        treatment_date = cleaned_data.get('treatment_date')
        certificate_number = cleaned_data.get('certificate_number')
        certificate_file = cleaned_data.get('certificate_file')
        
        # Validar método de tratamiento
        if treatment_method == 'OTHER' and not other_method:
            self.add_error(
                'other_method', 
                _('Debe especificar el método de tratamiento cuando se selecciona "Otro".')
            )
        
        # Validar campos basados en el estado seleccionado
        if status in ['IN_TRANSIT', 'DELIVERED', 'TREATED', 'CERTIFIED']:
            if not carrier:
                self.add_error('carrier', _('Se requiere el transportador para el estado actual.'))
            if not vehicle_plate:
                self.add_error('vehicle_plate', _('Se requiere la placa del vehículo para el estado actual.'))
        
        if status in ['DELIVERED', 'TREATED', 'CERTIFIED']:
            if not delivery_date:
                self.add_error('delivery_date', _('Se requiere la fecha de entrega para el estado actual.'))
        
        if status in ['TREATED', 'CERTIFIED']:
            if not treatment_date:
                self.add_error('treatment_date', _('Se requiere la fecha de tratamiento para el estado actual.'))
        
        if status == 'CERTIFIED':
            if not certificate_number:
                self.add_error('certificate_number', _('Se requiere el número de certificado para el estado "Certificado Emitido".'))
            
            # Solo requerir archivo si no existe uno previo
            instance = self.instance
            if not certificate_file and not (instance and instance.certificate_file):
                self.add_error('certificate_file', _('Se requiere el archivo de certificado para el estado "Certificado Emitido".'))
        
        # Validar fechas
        if delivery_date and cleaned_data.get('departure_date') and delivery_date < cleaned_data.get('departure_date'):
            self.add_error('delivery_date', _('La fecha de entrega no puede ser anterior a la fecha de salida.'))
        
        if treatment_date and delivery_date and treatment_date < delivery_date:
            self.add_error('treatment_date', _('La fecha de tratamiento no puede ser anterior a la fecha de entrega.'))
        
        return cleaned_data