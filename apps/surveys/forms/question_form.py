from django import forms
from django.utils.translation import gettext as _

from apps.surveys.models.surveymodel import Question, QuestionType


class QuestionForm(forms.ModelForm):
    """
    Formulario para la creación y edición de preguntas de encuestas
    """
    class Meta:
        model = Question
        fields = [
            'survey', 'question_type', 'text', 'help_text', 
            'is_required', 'order', 'min_value', 'max_value',
            'dependent_on', 'dependent_value'
        ]
        labels = {
            'survey': _('Encuesta'),
            'question_type': _('Tipo de pregunta'),
            'text': _('Pregunta'),
            'help_text': _('Texto de ayuda (opcional)'),
            'is_required': _('¿Es obligatoria?'),
            'order': _('Orden'),
            'min_value': _('Valor mínimo (opcional)'),
            'max_value': _('Valor máximo (opcional)'),
            'dependent_on': _('Pregunta dependiente (opcional)'),
            'dependent_value': _('Valor de la pregunta dependiente (opcional)')
        }
        widgets = {
            'survey': forms.HiddenInput(),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control','placeholder': _('Ingrese la pregunta')}),
            'help_text': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': _('Texto de ayuda opcional')}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Valor mínimo')}),
            'max_value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Valor máximo')}),
            'dependent_on': forms.Select(attrs={'class': 'form-control'}),
            'dependent_value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Valor de la pregunta dependiente')}),
        }
    
    def __init__(self, *args, **kwargs):
        """Inicialización personalizada del formulario"""
        # Extraer survey_id si viene proporcionado
        survey_id = kwargs.pop('survey_id', None)
        super().__init__(*args, **kwargs)
        
        # Configurar queryset para los tipos de preguntas
        self.fields['question_type'].queryset = QuestionType.objects.filter(is_active=True)
        self.fields['question_type'].empty_label = _("Seleccione tipo de pregunta")
        
        # Si se ha proporcionado survey_id, limitar las preguntas dependientes a la misma encuesta
        instance = kwargs.get('instance')
        
        if survey_id:
            # Para formulario de creación
            self.fields['dependent_on'].queryset = Question.objects.filter(
                survey_id=survey_id,
                is_active=True
            ).exclude(id=getattr(instance, 'id', None))
        elif instance and instance.pk:
            # Para formulario de edición
            self.fields['dependent_on'].queryset = Question.objects.filter(
                survey=instance.survey,
                is_active=True
            ).exclude(id=instance.id)
        else:
            # Si no hay survey_id ni instancia, desactivar el campo
            self.fields['dependent_on'].queryset = Question.objects.none()
            
        self.fields['dependent_on'].empty_label = _("Ninguna (siempre mostrar)")
        
        # Configurar campos condicionales basados en el tipo de pregunta
        self.fields['min_value'].required = False
        self.fields['max_value'].required = False
        
    def clean(self):
        """Validación a nivel de formulario"""
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        min_value = cleaned_data.get('min_value')
        max_value = cleaned_data.get('max_value')
        
        # Validar campos de rango para preguntas numéricas
        # Cambiado de QuestionType.NUMERIC a QuestionType.NUMBER
        if question_type and question_type.name == QuestionType.NUMBER:
            if min_value is not None and max_value is not None and min_value >= max_value:
                self.add_error('max_value', _('El valor máximo debe ser mayor que el valor mínimo'))
            
        # Validar campos de dependencia
        dependent_on = cleaned_data.get('dependent_on')
        dependent_value = cleaned_data.get('dependent_value')
        
        if dependent_on and not dependent_value:
            self.add_error('dependent_value', _('Si selecciona una pregunta dependiente, debe especificar un valor'))
            
        return cleaned_data
        
    def save(self, commit=True):
        """Personalización al guardar el formulario"""
        instance = super().save(commit=False)
        
        # Limpiar campos no aplicables según el tipo de pregunta
        # Cambiado de QuestionType.NUMERIC a QuestionType.NUMBER
        question_type = instance.question_type
        if question_type and question_type.name != QuestionType.NUMBER:
            instance.min_value = None
            instance.max_value = None
            
        if commit:
            instance.save()
            
        return instance
    