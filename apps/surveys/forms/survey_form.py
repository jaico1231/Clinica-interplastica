from django import forms
from django.forms import inlineformset_factory, modelformset_factory
from django.utils.translation import gettext_lazy as _

from apps.surveys.models.surveymodel import (
    Survey, QuestionType, Question, QuestionChoice,
    Response, Answer, AnswerChoice, Period, Indicator
    )


class SurveyForm(forms.ModelForm):
    """Form for creating and updating surveys"""
    class Meta:
        model = Survey
        fields = ['title', 'description', 'is_published', 'start_date', 'end_date']
        labels = {
            'title': _('Titulo Encuesta'),
            'description': _('Descripción'),
            'is_published': _('¿Publicar encuesta?'),
            'start_date': _('Fecha de inicio'),
            'end_date': _('Fecha de cierre'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter survey title')}),
            'description': forms.Textarea(attrs={'class': 'form-control','rows': 4}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control','type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control','type': 'date'}),
        }


# # Create formsets for managing multiple questions at once
# QuestionFormSet = modelformset_factory(
#     Question,
#     form=QuestionForm,
#     extra=3,
#     can_delete=True,
#     fields=[
#         'question_type', 'text', 'help_text', 'is_required', 'order',
#         'min_value', 'max_value'
#     ]
# )

# # Create formsets for managing multiple choices at once
# QuestionChoiceFormSet = inlineformset_factory(
#     Question, 
#     QuestionChoice, 
#     form=QuestionChoiceForm, 
#     extra=4, 
#     can_delete=True
# )


class ResponseForm(forms.ModelForm):
    """Form for creating survey responses"""
    respondent_email = forms.EmailField(
        label=_("Your Email (Optional)"),
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Response
        fields = ['respondent_email']
    
    def __init__(self, *args, **kwargs):
        """Initialize with dynamic fields based on survey questions"""
        super().__init__(*args, **kwargs)
        
        # We'll dynamically add form fields for each question when rendering the template
        # This is handled in the view's get_context_data and the template logic


class IndicatorFilterForm(forms.Form):
    """Form for filtering indicators by survey and period"""
    survey = forms.ModelChoiceField(
        queryset=Survey.objects.filter(is_active=True),
        required=False,
        empty_label="All Surveys",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    period = forms.ModelChoiceField(
        queryset=Period.objects.filter(is_active=True).order_by('-start_date'),
        required=False,
        empty_label="All Periods",
        widget=forms.Select(attrs={'class': 'form-select select2', 'data-placeholder': 'Select a period'})
    )
    
    category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by category'})
    )


class PeriodForm(forms.ModelForm):
    """Form for creating and updating periods"""
    class Meta:
        model = Period
        fields = ['name', 'month', 'year', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class IndicatorForm(forms.ModelForm):
    """Form for creating and updating indicators"""
    class Meta:
        model = Indicator
        fields = ['name', 'description', 'category', 'count_value', 'numeric_value', 'percentage_value']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'count_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'numeric_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'percentage_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }