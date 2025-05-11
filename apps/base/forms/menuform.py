from django import forms
from apps.base.models.menu import Menu, MenuItem

class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['name', 'group', 'is_active', 'icon']
        labels = {
            'name': 'Nombre',
            'group': 'Grupos',
            'is_active': 'Activo',
            'icon': 'Icono',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['menu', 'name', 'url_name', 'icon', 'is_active', 'groups']
        lables = {
            'menu': 'Menú',
            'name': 'Nombre',
            'url_name': 'URL',
            'icon': 'Icono',
            'is_active': 'Activo',
            'groups': 'Grupos',
        }
        widgets = {
            'menu': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url_name': forms.TextInput(attrs={'class': 'form-control'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-control'}),
            # is_active deshabilitado para evitar que se modifique
            'is_active': forms.HiddenInput(),
            # Asegurarse de que la URL sea una URL válida
            'url_name': forms.TextInput(attrs={'class': 'form-control', 'pattern': '^[a-zA-Z0-9_\-]+$'}),
            # Asegurarse de que el icono sea un icono válido
            'icon': forms.TextInput(attrs={'class': 'form-control', 'pattern': '^[a-zA-Z0-9_\-]+$'}),
            
        }
