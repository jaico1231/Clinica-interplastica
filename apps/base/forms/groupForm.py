from django import forms
from django.contrib.auth.models import Group, Permission

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {
            'name': 'Nombre del Grupo',
            'permissions': 'Permisos'
        }
        widgets = {
            'permissions': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '10'
            })
        }

class GroupFormCreate(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {
            'name': 'Nombre del Grupo',
            'permissions': 'Permisos'
        }
        widgets = {
            'permissions': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '10'
            })
        }