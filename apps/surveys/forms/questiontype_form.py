from django import forms
from django.utils.translation import gettext_lazy as _
from apps.surveys.models.surveymodel import QuestionType

class QuestionTypeForm(forms.ModelForm):
    """
    Formulario para crear y editar tipos de preguntas
    """
    
    class Meta:
        model = QuestionType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('Nombre del tipo de pregunta'),
                    'autocomplete': 'off',
                    'autofocus': True
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('Descripción del tipo de pregunta'),
                    'rows': 3,
                    'autocomplete': 'off'
                }
            )
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Marcar todos los campos como requeridos
        for field_name, field in self.fields.items():
            if field_name == 'description':
                field.required = False
            else:
                field.required = True
    
    def clean_name(self):
        """
        Validación personalizada para el campo nombre
        """
        name = self.cleaned_data['name']
        
        # Convertir a mayúsculas y eliminar espacios en blanco
        name = name.strip().upper()
        
        # Verificar si ya existe un tipo de pregunta con este nombre
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # Si estamos editando, excluir el objeto actual de la validación
            exists = QuestionType.objects.filter(name=name).exclude(pk=instance.pk).exists()
        else:
            # Si estamos creando, verificar que no exista un objeto con el mismo nombre
            exists = QuestionType.objects.filter(name=name).exists()
            
        if exists:
            raise forms.ValidationError(_('Ya existe un tipo de pregunta con este nombre'))
            
        return name
        
    def clean(self):
        """
        Validación global del formulario
        """
        cleaned_data = super().clean()
        
        # Aquí podemos agregar reglas de validación adicionales
        # que involucren a múltiples campos
        
        return cleaned_data