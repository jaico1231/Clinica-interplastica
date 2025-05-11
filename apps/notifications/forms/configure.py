# apps/notifications/forms/configure.py

from django import forms
from django.utils.translation import gettext_lazy as _
from apps.notifications.models.emailmodel import EmailConfiguration, SMSConfiguration, WhatsAppConfiguration

class EmailConfigurationForm(forms.ModelForm):
    """Formulario para la configuración de email"""
    
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
            'id': 'password-field'
        }),
        required=False,
        help_text="Ingrese nueva contraseña o deje en blanco para mantener la actual."
    )
    
    api_key = forms.CharField(
        label="Clave API",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Clave secreta',
            'autocomplete': 'new-password',
            'id': 'api-key-field'
        }),
        required=False,
        help_text="Ingrese nueva clave API o deje en blanco para mantener la actual."
    )

    class Meta:
        model = EmailConfiguration
        fields = [
            'name', 'backend', 'host', 'port', 'username', 'password',
            'api_key', 'security_protocol', 'timeout', 'from_email',
            'is_active', 'use_custom_headers', 'custom_headers', 'fail_silently'
        ]
        labels = {
            'name': 'Nombre de la Configuración',
            'backend': 'Proveedor de Correo',
            'host': 'Servidor de Correo',
            'port': 'Puerto',
            'username': 'Usuario',
            'security_protocol': 'Protocolo de Seguridad',
            'timeout': 'Tiempo de Espera (segundos)',
            'from_email': 'Correo Remitente',
            'is_active': 'Activo',
            'use_custom_headers': 'Usar Cabeceras Personalizadas',
            'custom_headers': 'Cabeceras Personalizadas',
            'fail_silently': 'Fallar Silenciosamente'
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Configuración Gmail'
            }),
            'host': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: smtp.gmail.com'
            }),
            'port': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 65535
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: usuario@dominio.com'
            }),
            'security_protocol': forms.Select(attrs={
                'class': 'form-select'
            }),
            'timeout': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'from_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: no-responder@empresa.com'
            }),
            'custom_headers': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ej: {"X-Priority": 1, "X-MSMail-Priority": "High"}'
            }),
            'backend': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def clean(self):
        """
        Validación adicional para asegurar que se proporcione
        contraseña cuando es necesario
        """
        cleaned_data = super().clean()
        backend = cleaned_data.get('backend')
        password = cleaned_data.get('password')
        
        # Si es SMTP, verifica que tenga contraseña (para formulario de creación)
        if backend == EmailConfiguration.EmailBackend.SMTP and not self.instance.pk and not password:
            self.add_error('password', 'La contraseña es obligatoria para servidores SMTP.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Sobrescribe el método save para manejar correctamente la contraseña y API key
        """
        instance = super().save(commit=False)
        
        # Si el formulario está para un objeto existente (actualización)
        if instance.pk:
            # Obtener el objeto existente de la base de datos
            old_instance = EmailConfiguration.objects.get(pk=instance.pk)
            
            # Si la contraseña está vacía, mantener la actual
            if not self.cleaned_data.get('password'):
                instance.password = old_instance.password
            
            # Si la API key está vacía, mantener la actual
            if not self.cleaned_data.get('api_key'):
                instance.api_key = old_instance.api_key
        
        if commit:
            instance.save()
        
        return instance

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # Personalización adicional de labels
    #     self.fields['fail_silently'].label = "No mostrar errores públicamente"
    #     self.fields['is_active'].label = "Configuración activa"
        
    #     # Ordenar opciones del selector de backend
    #     self.fields['backend'].choices = sorted(
    #         self.fields['backend'].choices,
    #         key=lambda x: x[1]
    #     )
        
    #     # Para creación, marcar campos sensibles como obligatorios según el backend
    #     if not self.instance.pk:  # Si es creación (no tiene pk)
    #         backend = self.initial.get('backend', None)
    #         if backend == EmailConfiguration.EmailBackend.SENDGRID:
    #             self.fields['api_key'].required = True
    #         elif backend == EmailConfiguration.EmailBackend.SMTP:
    #             self.fields['password'].required = True

    # def clean(self):
    #     cleaned_data = super().clean()
    #     backend = cleaned_data.get('backend')
    #     is_creation = not self.instance.pk  # Verifica si es una creación

    #     # Validar campos obligatorios para creación y actualización
    #     if backend == EmailConfiguration.EmailBackend.SENDGRID:
    #         if not cleaned_data.get('api_key') and (is_creation or not self.instance.api_key):
    #             self.add_error('api_key', 'La API key es obligatoria para SendGrid.')
    #     elif backend == EmailConfiguration.EmailBackend.SMTP:
    #         if not cleaned_data.get('password') and (is_creation or not self.instance.password):
    #             self.add_error('password', 'La contraseña es obligatoria para SMTP.')
        
    #     return cleaned_data

    # def save(self, commit=True):
    #     instance = super().save(commit=False)
        
    #     # Si es creación o los campos están presentes, actualizarlos
    #     if not instance.pk:
    #         instance.password = self.cleaned_data.get('password', '')
    #         instance.api_key = self.cleaned_data.get('api_key', '')
    #     else:
    #         # Mantener lógica original para actualización
    #         if not self.cleaned_data.get('password'):
    #             instance.password = EmailConfiguration.objects.get(pk=instance.pk).password
    #         if not self.cleaned_data.get('api_key'):
    #             instance.api_key = EmailConfiguration.objects.get(pk=instance.pk).api_key
        
    #     if commit:
    #         instance.save()
    #     return instance


class SMSConfigurationForm(forms.ModelForm):
    """Formulario para la configuración de SMS"""
    account_sid = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Enter new SID/Key or leave blank to keep current."
    )
    auth_token = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Enter new Auth Token or leave blank to keep current."
    )
    api_key = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Enter new API Key or leave blank to keep current."
    )

    class Meta:
        model = SMSConfiguration
        fields = [
            'name', 'backend', 'account_sid', 'auth_token', 'phone_number',
            'api_key', 'region', 'timeout', 'is_active'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['account_sid'].required = False
            self.fields['auth_token'].required = False
            self.fields['api_key'].required = False

    def clean_account_sid(self):
        return self.cleaned_data.get('account_sid') or None

    def clean_auth_token(self):
        return self.cleaned_data.get('auth_token') or None

    def clean_api_key(self):
        return self.cleaned_data.get('api_key') or None

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not self.cleaned_data.get('account_sid') and instance.pk:
            instance.account_sid = SMSConfiguration.objects.get(pk=instance.pk).account_sid
        if not self.cleaned_data.get('auth_token') and instance.pk:
            instance.auth_token = SMSConfiguration.objects.get(pk=instance.pk).auth_token
        if not self.cleaned_data.get('api_key') and instance.pk:
            instance.api_key = SMSConfiguration.objects.get(pk=instance.pk).api_key

        if commit:
            instance.save()
            self._save_m2m()
        return instance


class WhatsAppConfigurationForm(forms.ModelForm):
    """Formulario para la configuración de WhatsApp"""
    account_sid = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Enter new SID or leave blank to keep current."
    )
    auth_token = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Enter new Auth Token or leave blank to keep current."
    )

    class Meta:
        model = WhatsAppConfiguration
        fields = [
            'name', 'backend', 'account_sid', 'auth_token', 'whatsapp_number',
            'business_id', 'api_version', 'timeout', 'is_active'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['account_sid'].required = False
            self.fields['auth_token'].required = False

    def clean_account_sid(self):
        return self.cleaned_data.get('account_sid') or None

    def clean_auth_token(self):
        return self.cleaned_data.get('auth_token') or None

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not self.cleaned_data.get('account_sid') and instance.pk:
            instance.account_sid = WhatsAppConfiguration.objects.get(pk=instance.pk).account_sid
        if not self.cleaned_data.get('auth_token') and instance.pk:
            instance.auth_token = WhatsAppConfiguration.objects.get(pk=instance.pk).auth_token

        if commit:
            instance.save()
            self._save_m2m()
        return instance