# Create your views here.
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.third_party.models.third_party import ThirdParty
from apps.base.models.users import User
from apps.base.models.support import City, State

class ThirdPartyForm(forms.ModelForm):
    """
    Formulario para crear y editar terceros con manejo de relaciones y validaciones
    """
    class Meta:
        model = ThirdParty
        fields = [
            'first_name', 'last_name', 'company_name', 'trade_name',
            'document_type', 'document_number', 'address', 'landline', 
            'mobile', 'email', 'country', 'state', 'city', 
            'third_party_type', 'advisor', 
            'tax_regime', 'tax_responsibility', 'economic_activity', 'image'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nombre')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Apellido')}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Razón Social')}),
            'trade_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nombre Comercial')}),
            'document_type': forms.Select(attrs={'class': 'form-select select2'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Número de Documento')}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Dirección')}),
            'landline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Teléfono Fijo')}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Teléfono Móvil')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Correo Electrónico')}),
            'country': forms.Select(attrs={'class': 'form-select select2'}),
            'state': forms.Select(attrs={'class': 'form-select select2'}),
            'city': forms.Select(attrs={'class': 'form-select select2'}),
            'third_party_type': forms.Select(attrs={'class': 'form-select select2'}),
            'advisor': forms.Select(attrs={'class': 'form-select select2'}),
            'tax_regime': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Régimen Tributario')}),
            'tax_responsibility': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Responsabilidad Fiscal')}),
            'economic_activity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Actividad Económica')}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
        
    #     # Hacer que ciertos campos sean requeridos
    #     self.fields['document_type'].required = True
    #     self.fields['document_number'].required = True
    #     self.fields['country'].required = True
    #     self.fields['state'].required = True
    #     self.fields['city'].required = True
    #     self.fields['third_party_type'].required = True
        
    #     # Filtrar asesores activos para el selector
    #     self.fields['advisor'].queryset = User.objects.filter(is_active=True)
        
    #     # Estado por defecto: Activo
    #     self.fields['status'].initial = True
        
    #     # Etiquetas personalizadas
    #     self.fields['status'].label = _('¿Activo?')
        
    #     # Configuración de selectores dependientes (país -> estado -> ciudad)
    #     instance = kwargs.get('instance')
        
    #     # Si es una edición (hay instancia), configurar selectores dependientes
    #     if instance:
    #         # Si hay país, cargar estados
    #         if instance.country:
    #             self.fields['state'].queryset = State.objects.filter(country=instance.country)
    #         else:
    #             self.fields['state'].queryset = State.objects.none()
                
    #         # Si hay estado, cargar ciudades
    #         if instance.state:
    #             self.fields['city'].queryset = City.objects.filter(state=instance.state)
    #         else:
    #             self.fields['city'].queryset = City.objects.none()
    #     else:
    #         # Para nuevos terceros, inicializar con queryset vacío
    #         self.fields['state'].queryset = State.objects.none()
    #         self.fields['city'].queryset = City.objects.none()
    
    def clean(self):
        """
        Validaciones personalizadas del formulario
        """
        cleaned_data = super().clean()
        
        # Validar que se tiene al menos nombre o razón social
        first_name = cleaned_data.get('first_name')
        company_name = cleaned_data.get('company_name')
        
        if not first_name and not company_name:
            raise ValidationError(_('Debe proporcionar al menos el nombre o la razón social'))
        
        # Si es persona natural, requerir apellido
        third_party_type = cleaned_data.get('third_party_type')
        last_name = cleaned_data.get('last_name')
        
        if third_party_type and third_party_type.name == 'Persona Natural' and not last_name and first_name:
            self.add_error('last_name', _('El apellido es requerido para personas naturales'))
        
        # Si es persona jurídica, requerir razón social
        if third_party_type and third_party_type.name == 'Persona Jurídica' and not company_name:
            self.add_error('company_name', _('La razón social es requerida para personas jurídicas'))
        
        # Validar que país, estado y ciudad sean consistentes
        country = cleaned_data.get('country')
        state = cleaned_data.get('state')
        city = cleaned_data.get('city')
        
        if country and state and state.country != country:
            self.add_error('state', _('El departamento seleccionado no pertenece al país'))
            
        if state and city and city.state != state:
            self.add_error('city', _('La ciudad seleccionada no pertenece al departamento'))
        
        return cleaned_data
    
    def clean_document_number(self):
        """
        Validar que el número de documento sea único
        """
        document_number = self.cleaned_data.get('document_number')
        instance = self.instance
        
        # Verificar si ya existe un tercero con ese documento (excluyendo la instancia actual)
        if ThirdParty.objects.filter(document_number=document_number).exclude(pk=getattr(instance, 'pk', None)).exists():
            raise ValidationError(_('Ya existe un tercero con este número de documento'))
            
        return document_number
    
    def clean_email(self):
        """
        Validar que el email sea único (si se proporciona)
        """
        email = self.cleaned_data.get('email')
        instance = self.instance
        
        # Si se proporciona email, verificar que sea único
        if email and ThirdParty.objects.filter(email=email).exclude(pk=getattr(instance, 'pk', None)).exists():
            raise ValidationError(_('Ya existe un tercero con este correo electrónico'))
            
        return email