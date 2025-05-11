from django import forms
from django.utils.translation import gettext_lazy as _
from apps.surveys.models.surveymodel import Response, QuestionType

class ResponseForm(forms.ModelForm):
    """
    Form for survey responses.
    Handles both anonymous and authenticated users.
    Additional fields for specific question types will be added dynamically.
    """
    
    def __init__(self, *args, **kwargs):
        # Get the user from kwargs if available
        self.user = kwargs.pop('user', None)
        self.survey = kwargs.pop('survey', None)
        
        super().__init__(*args, **kwargs)
        
        # If user is authenticated, make respondent fields optional 
        # and fill them with user data as initial values
        if self.user and self.user.is_authenticated:
            self.fields['respondent_name'].required = False
            self.fields['respondent_email'].required = False
            
            # Set initial values from user
            self.fields['respondent_name'].initial = self.user.get_full_name()
            self.fields['respondent_email'].initial = self.user.email
            
            # Add help text explaining why we're asking this info
            self.fields['respondent_name'].help_text = _('Ya estamos usando su nombre de usuario, pero puede cambiarlo si lo desea.')
            self.fields['respondent_email'].help_text = _('Ya estamos usando su correo registrado, pero puede cambiarlo si lo desea.')
        
        # Customize fields if survey is available
        if self.survey:
            # Set a different help text for anonymous vs authenticated users
            if not self.user or not self.user.is_authenticated:
                self.fields['respondent_email'].help_text = _('Su correo electrónico no será compartido y solo se usará para contactarlo si es necesario.')
                self.fields['respondent_name'].help_text = _('Ingrese su nombre completo')
                
                # Make the fields required for anonymous users
                self.fields['respondent_name'].required = True
                self.fields['respondent_email'].required = True
    
    class Meta:
        model = Response
        fields = ['respondent_name', 'respondent_email']
        
        widgets = {
            'respondent_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese su nombre completo'),
                'title': _('Ingrese su nombre completo')
            }),
            'respondent_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('ejemplo@correo.com'),
                'title': _('Ingrese su dirección de correo electrónico')
            })
        }
        
        labels = {
            'respondent_name': _('Nombre'),
            'respondent_email': _('Correo Electrónico')
        }
    
    def clean(self):
        """
        Custom validation for the form.
        Ensures that anonymous responses provide contact information.
        """
        cleaned_data = super().clean()
        respondent_name = cleaned_data.get('respondent_name')
        respondent_email = cleaned_data.get('respondent_email')
        
        # If user is not authenticated, ensure they provided contact info
        if not self.user or not self.user.is_authenticated:
            if not respondent_name:
                self.add_error('respondent_name', _('Por favor proporcione su nombre para continuar.'))
            
            if not respondent_email:
                self.add_error('respondent_email', _('Por favor proporcione un correo electrónico para continuar.'))
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Save the response with the user information.
        If user is authenticated, use their info regardless of form fields.
        """
        response = super().save(commit=False)
        
        # If user is authenticated, set the respondent directly
        if self.user and self.user.is_authenticated:
            response.respondent = self.user
            
            # Only use form data if provided, otherwise use user data
            if not response.respondent_name:
                response.respondent_name = self.user.get_full_name()
            
            if not response.respondent_email:
                response.respondent_email = self.user.email
        
        if commit:
            response.save()
        
        return response