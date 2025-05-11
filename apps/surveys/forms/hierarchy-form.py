from django import forms
from django.utils.translation import gettext_lazy as _
from apps.encuestas.models import HierarchyItem, Question
from apps.base.models.support import QuestionType


class HierarchyItemForm(forms.ModelForm):
    """Form for creating and updating hierarchy items"""
    parent_id = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = HierarchyItem
        fields = ['text', 'description', 'order', 'is_draggable', 'is_editable', 'icon', 'custom_class']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Item text')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Optional description')}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Icon class (e.g. bi-star)')}),
            'custom_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Custom CSS class')}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_draggable'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['is_editable'].widget.attrs.update({'class': 'form-check-input'})
    
    def clean(self):
        cleaned_data = super().clean()
        parent_id = cleaned_data.get('parent_id')
        
        # Handle parent relationship
        if parent_id:
            try:
                parent = HierarchyItem.objects.get(id=parent_id)
                self.instance.parent = parent
            except HierarchyItem.DoesNotExist:
                self.instance.parent = None
        else:
            self.instance.parent = None
        
        return cleaned_data


class QuestionCreateForm(forms.ModelForm):
    """Form for creating questions with type-specific options"""
    question_type = forms.ModelChoiceField(
        queryset=QuestionType.objects.all(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Question
        fields = [
            'text', 'help_text', 'question_type', 'is_required', 
            'min_value', 'max_value', 'allow_hierarchy_creation', 
            'display_hierarchy_as'
        ]
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Question text')}),
            'help_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Additional instructions for respondents')}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'min_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'allow_hierarchy_creation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_hierarchy_as': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        survey = kwargs.pop('survey', None)
        question_type_name = kwargs.pop('question_type_name', None)
        
        super().__init__(*args, **kwargs)
        
        if survey:
            self.instance.survey = survey
        
        # Set initial question type if provided
        if question_type_name:
            try:
                question_type = QuestionType.objects.get(name=question_type_name.upper())
                self.fields['question_type'].initial = question_type.id
            except QuestionType.DoesNotExist:
                pass
        
        # Show/hide fields based on question type
        self.fields['min_value'].widget = forms.HiddenInput()
        self.fields['max_value'].widget = forms.HiddenInput()
        self.fields['allow_hierarchy_creation'].widget = forms.HiddenInput()
        self.fields['display_hierarchy_as'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        
        # Validate based on question type
        if question_type:
            if question_type.name == QuestionType.NUMBER:
                # For number questions, validate min and max
                min_value = cleaned_data.get('min_value')
                max_value = cleaned_data.get('max_value')
                
                if min_value is not None and max_value is not None and min_value > max_value:
                    self.add_error('min_value', _('Minimum value cannot be greater than maximum value'))
            
            # Clear irrelevant fields based on question type
            if question_type.name != QuestionType.NUMBER:
                cleaned_data['min_value'] = None
                cleaned_data['max_value'] = None
            
            if question_type.name != QuestionType.HIERARCHY:
                cleaned_data['allow_hierarchy_creation'] = False
                cleaned_data['display_hierarchy_as'] = 'LIST'
        
        return cleaned_data


class HierarchyAnswerForm(forms.ModelForm):
    """Form for respondents to provide hierarchy answers"""
    item_order = forms.CharField(widget=forms.HiddenInput(), required=True)
    
    class Meta:
        model = HierarchyAnswer
        fields = ['item', 'custom_text']
        widgets = {
            'item': forms.HiddenInput(),
            'custom_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Custom text (optional)')}),
        }
    
    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question', None)
        super().__init__(*args, **kwargs)
        
        if question:
            self.fields['item'].queryset = HierarchyItem.objects.filter(question=question)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Parse the item order to set position
        try:
            item_order = self.cleaned_data.get('item_order')
            position_data = json.loads(item_order)
            
            # Find position for this item
            item_id = str(self.cleaned_data.get('item').id)
            if item_id in position_data:
                instance.position = position_data[item_id]
            else:
                # Default to the end
                instance.position = len(position_data)
        except (json.JSONDecodeError, ValueError, TypeError):
            # Default to position 0 if there's an error
            instance.position = 0
        
        if commit:
            instance.save()
        
        return instance