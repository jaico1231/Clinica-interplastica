# apps/base/forms/user_forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from apps.base.models.users import User


class UserForm(forms.ModelForm):
    """
    Formulario personalizado para la creación y edición de usuarios
    """
    password = forms.CharField(
        label=_("Contraseña"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Contraseña')}),
        required=False  # Será requerido en el clean() para nuevos usuarios
    )
    
    password_confirm = forms.CharField(
        label=_("Confirmar contraseña"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Confirmar contraseña')}),
        required=False  # Será requerido en el clean() para nuevos usuarios
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 
            'identification_type', 'identification_number',
            'is_active', 'is_staff', 'groups'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nombre de usuario')}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nombres')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Apellidos')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Correo electrónico')}),
            'identification_type': forms.Select(attrs={'class': 'form-select'}),
            'identification_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Número de identificación')}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-select select2', 'multiple': 'multiple'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Definir campos requeridos
        self.fields['username'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['identification_type'].required = True
        self.fields['identification_number'].required = True
        
        # Configurar etiquetas específicas
        self.fields['is_active'].label = _('Usuario activo')
        self.fields['is_staff'].label = _('Acceso al admin')
        self.fields['groups'].label = _('Grupos')
        
        # Si es un usuario existente, el password no es requerido
        if self.instance.pk:
            self.fields['password'].help_text = _('Dejar en blanco para mantener la contraseña actual')
            self.fields['password_confirm'].help_text = _('Dejar en blanco para mantener la contraseña actual')
        else:
            # Para nuevos usuarios, la contraseña es requerida
            self.fields['password'].required = True
            self.fields['password_confirm'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        # Validar que las contraseñas coincidan si se está estableciendo una nueva
        if password:
            if password != password_confirm:
                self.add_error('password_confirm', _('Las contraseñas no coinciden'))
            
            # Validar complejidad de la contraseña
            if len(password) < 8:
                self.add_error('password', _('La contraseña debe tener al menos 8 caracteres'))
        
        # Si es un nuevo usuario, la contraseña es obligatoria
        elif not self.instance.pk:
            self.add_error('password', _('Este campo es obligatorio para nuevos usuarios'))
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Establecer contraseña si se proporciona una nueva
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
            # Guardar las relaciones m2m
            self._save_m2m()
        
        return user


class PasswordChangeForm(forms.Form):
    """
    Formulario para cambiar la contraseña de un usuario existente
    """
    password1 = forms.CharField(
        label=_('Nueva contraseña'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Nueva contraseña')}),
        required=True
    )
    
    password2 = forms.CharField(
        label=_('Confirmar contraseña'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Confirmar contraseña')}),
        required=True
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', _('Las contraseñas no coinciden'))
            
            # Validar complejidad de la contraseña
            if len(password1) < 8:
                self.add_error('password1', _('La contraseña debe tener al menos 8 caracteres'))
        
        return cleaned_data
    """Formulario para cambio de contraseña"""
    password1 = forms.CharField(
        label="Nueva contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )
    
    def clean_password2(self):
        """Verifica que las dos contraseñas coincidan"""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden.")
        
        # Validar complejidad de contraseña
        try:
            validate_password(password2)
        except ValidationError as e:
            self.add_error('password2', e)
            
        return password2