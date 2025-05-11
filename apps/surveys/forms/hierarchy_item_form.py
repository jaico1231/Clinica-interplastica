from django import forms
from django.utils.translation import gettext_lazy as _

from apps.surveys.models.surveymodel import HierarchyItem
# from apps.encuestas.models import HierarchyItem, Question


class HierarchyItemForm(forms.ModelForm):
    """Form for creating and updating hierarchy items"""
    parent_id = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = HierarchyItem
        fields = [
            'text', 
            'description', 
            'order', 
            'is_draggable', 
            'is_editable', 
            'icon', 
            'custom_class']
        labels = {
            'text': _('Item'),
            'description': _('descripcion (opcional)'),
            'order': _('Orden'),
            'is_draggable': _('Es arrastrable'),
            'is_editable': _('Es editable'),
            'icon': _('Icono (opcional)'),
            'custom_class': _('Clase CSS personalizada (opcional)'),
        }
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
        
        # If this is an existing item, set initial parent_id
        if self.instance and self.instance.pk and self.instance.parent:
            self.initial['parent_id'] = self.instance.parent.id
    
    def clean(self):
        cleaned_data = super().clean()
        parent_id = cleaned_data.get('parent_id')
        
        # Handle parent relationship
        if parent_id:
            try:
                parent = HierarchyItem.objects.get(id=parent_id)
                
                # Check for circular references if this is an existing item
                if self.instance and self.instance.pk:
                    if str(self.instance.id) == parent_id:
                        self.add_error('parent_id', _('An item cannot be its own parent'))
                    
                    # Check if parent is a descendant of the item
                    descendants = self.instance.get_children_recursive()
                    if parent in descendants:
                        self.add_error('parent_id', _('Cannot select a descendant as parent'))
                
                # Store parent for later use in save method
                self.parent = parent
            except HierarchyItem.DoesNotExist:
                self.parent = None
        else:
            self.parent = None
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set parent based on cleaned parent_id
        if hasattr(self, 'parent'):
            instance.parent = self.parent
        
        if commit:
            instance.save()
        
        return instance
