from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class LoginForm(AuthenticationForm):
    """
    Formulario personalizado para inicio de sesión con funcionalidad Remember Me
    """
    username = forms.CharField(
        label=_("Usuario"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Nombre de usuario'),
            'autofocus': True,
            'autocomplete': 'username'
        })
    )
    
    password = forms.CharField(
        label=_("Contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Contraseña'),
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        label=_("Recordar sesión"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    error_messages = {
        'invalid_login': _(
            "Por favor introduzca un nombre de usuario y contraseña correctos. "
            "Note que ambos campos pueden ser sensibles a mayúsculas."
        ),
        'inactive': _("Esta cuenta está inactiva."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mejora de accesibilidad
        self.fields['remember_me'].help_text = _("Mantener sesión iniciada durante 14 días")

    def confirm_login_allowed(self, user):
        """
        Valida si el usuario puede iniciar sesión
        """
        super().confirm_login_allowed(user)
        # Aquí puedes agregar validaciones adicionales si es necesario

    class Meta:
        model = User
        fields = ('username', 'password')  # Removido remember_me que no es campo del modelo