from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from apps.accounting.models.PUC import (
    Naturaleza, GrupoCuenta, CuentaMayor, 
    SubCuenta, CuentaDetalle, CuentaAuxiliar
)

class NaturalezaForm(forms.ModelForm):
    """Formulario para crear/editar Naturalezas"""
    
    class Meta:
        model = Naturaleza
        fields = ['code', 'name', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 1, 'pattern': '[1-9]'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            if not code.isdigit():
                raise forms.ValidationError(_('El código debe ser un dígito numérico'))
        return code

class GrupoCuentaForm(forms.ModelForm):
    """Formulario para crear/editar Grupos de Cuenta"""
    
    class Meta:
        model = GrupoCuenta
        fields = ['code', 'name', 'naturaleza', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 4, 'pattern': '[1-9][0-9]{0,3}'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'naturaleza': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si se proporciona naturaleza en initial, bloquear el campo
        if 'initial' in kwargs and 'naturaleza' in kwargs['initial']:
            self.fields['naturaleza'].widget.attrs['readonly'] = True
        
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            if not code.isdigit():
                raise forms.ValidationError(_('El código debe ser numérico'))
            
            # Verificar longitud (1 a 4 dígitos)
            if len(code) < 1 or len(code) > 4:
                raise forms.ValidationError(_('El código debe tener entre 1 y 4 dígitos'))
        return code

class CuentaMayorForm(forms.ModelForm):
    """Formulario para crear/editar Cuentas Mayor"""
    
    class Meta:
        model = CuentaMayor
        fields = ['code', 'name', 'naturaleza', 'grupo', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 6, 'pattern': '[1-9][0-9]{0,5}'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'naturaleza': forms.Select(attrs={'class': 'form-select'}),
            'grupo': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si se proporciona grupo en initial, bloquear el campo
        if 'initial' in kwargs:
            if 'grupo' in kwargs['initial']:
                self.fields['grupo'].widget.attrs['readonly'] = True
            if 'naturaleza' in kwargs['initial']:
                self.fields['naturaleza'].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        grupo = cleaned_data.get('grupo')
        
        if code and grupo:
            # Verificar que el código comienza con el código del grupo
            if not code.startswith(grupo.code[:1]):
                self.add_error('code', _(f'El código debe comenzar con {grupo.code[:1]}'))
        
        return cleaned_data

class SubCuentaForm(forms.ModelForm):
    # Campo level con valor predeterminado 3
    level = forms.IntegerField(
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        label=_('Nivel')
    )
    
    # Campo de visualización de la cuenta mayor (solo lectura)
    cuenta_mayor_display = forms.CharField(
        label=_('Cuenta Mayor'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    class Meta:
        model = SubCuenta
        fields = ['code', 'name', 'naturaleza', 'level', 'cuenta_mayor', 'description']
        labels = {
            'code': _('Código'),
            'name': _('Nombre'),
            'naturaleza': _('Naturaleza'),
            'cuenta_mayor': _('Cuenta Mayor'),
            'description': _('Descripción'),
        }
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control', 
                'maxlength': 4,  # Limitado a 4 dígitos para subcuentas
                'pattern': '[0-9]{4}',  # Patrón exacto de 4 dígitos
                'id': 'id_code_subcuenta'
            }),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'naturaleza': forms.Select(attrs={'class': 'form-select'}),
            'cuenta_mayor': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que el nivel siempre sea 3 para subcuentas
        self.initial['level'] = 3
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code:
            return code
            
        # Validar que el código tenga exactamente 4 dígitos
        if len(code) != 4:
            raise forms.ValidationError(_('El código debe tener exactamente 4 dígitos'))
        
        return code
    
    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        
        if code and len(code) == 4:
            # Obtener los primeros 2 dígitos para buscar la Cuenta Mayor (nivel 2)
            prefix = code[:2]
            
            try:
                cuenta_mayor = CuentaMayor.objects.get(code=prefix, level=2)
                cleaned_data['cuenta_mayor'] = cuenta_mayor
                
                # No es necesario verificar coherencia con el grupo, ya que
                # estamos tomando los primeros 2 dígitos directamente para la cuenta mayor
            except CuentaMayor.DoesNotExist:
                self.add_error('code', _('No existe una Cuenta Mayor (nivel 2) con el código: {}').format(prefix))
            except CuentaMayor.MultipleObjectsReturned:
                self.add_error('code', _('Existen múltiples Cuentas Mayores con el código: {}').format(prefix))
        
        return cleaned_data

class CuentaDetalleForm(forms.ModelForm):
    # Campo level con valor predeterminado 4
    level = forms.IntegerField(
        initial=4,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        label=_('Nivel')
    )
    
    # Campo de visualización de la subcuenta (solo lectura)
    subcuenta_display = forms.CharField(
        label=_('Subcuenta'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    class Meta:
        model = CuentaDetalle
        fields = ['code', 'name', 'naturaleza', 'level', 'subcuenta', 'description', 'is_tax_account']
        labels = {
            'code': _('Código'),
            'name': _('Nombre'),
            'naturaleza': _('Naturaleza'),
            'subcuenta': _('Subcuenta'),
            'description': _('Descripción'),
            'is_tax_account': _('Es cuenta fiscal'),
        }
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control', 
                'maxlength': 6,  # Limitado a 6 dígitos para cuentas detalle
                'pattern': '[0-9]{6}',  # Patrón exacto de 6 dígitos
                'id': 'id_code_cuenta_detalle'
            }),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'naturaleza': forms.Select(attrs={'class': 'form-select'}),
            'subcuenta': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_tax_account': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que el nivel siempre sea 4 para cuentas detalle
        self.initial['level'] = 4
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code:
            return code
            
        # Validar que el código tenga exactamente 6 dígitos
        if len(code) != 6:
            raise forms.ValidationError(_('El código debe tener exactamente 6 dígitos'))
        
        return code
    
    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        
        if code and len(code) == 6:
            # Obtener los primeros 4 dígitos para buscar la Subcuenta (nivel 3)
            prefix = code[:4]
            
            try:
                subcuenta = SubCuenta.objects.get(code=prefix, level=3)
                cleaned_data['subcuenta'] = subcuenta
                
                # Heredar la naturaleza de la subcuenta
                cleaned_data['naturaleza'] = subcuenta.naturaleza
                
            except SubCuenta.DoesNotExist:
                self.add_error('code', _('No existe una Subcuenta (nivel 3) con el código: {}').format(prefix))
            except SubCuenta.MultipleObjectsReturned:
                self.add_error('code', _('Existen múltiples Subcuentas con el código: {}').format(prefix))
        
        return cleaned_data


class CuentaAuxiliarForm(forms.ModelForm):
    # Campo level con valor predeterminado 5
    level = forms.IntegerField(
        initial=5,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        label=_('Nivel')
    )
    
    # Campo de visualización de la cuenta detalle (solo lectura)
    cuenta_detalle_display = forms.CharField(
        label=_('Cuenta Detalle'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    class Meta:
        model = CuentaAuxiliar
        fields = ['company', 'code', 'name', 'naturaleza', 'level', 'cuenta_detalle', 
                 'description', 'is_tax_account', 'allows_movements']
        labels = {
            'company': _('Empresa'),
            'code': _('Código'),
            'name': _('Nombre'),
            'naturaleza': _('Naturaleza'),
            'cuenta_detalle': _('Cuenta Detalle'),
            'description': _('Descripción'),
            'is_tax_account': _('Es cuenta fiscal'),
            'allows_movements': _('Permite movimientos'),
        }
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={
                'class': 'form-control', 
                'maxlength': 20,  # Según el modelo permite hasta 20 caracteres
                'pattern': '[0-9]{6,20}',  # Debe comenzar con los 6 dígitos de la cuenta detalle
                'id': 'id_code_cuenta_auxiliar'
            }),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'naturaleza': forms.Select(attrs={'class': 'form-select'}),
            'cuenta_detalle': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_tax_account': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allows_movements': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que el nivel siempre sea 5 para cuentas auxiliares
        self.initial['level'] = 5
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code:
            return code
            
        # Validar que el código tenga al menos 6 dígitos
        if len(code) < 6:
            raise forms.ValidationError(_('El código debe tener al menos 6 dígitos'))
        
        return code
    
    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        
        if code and len(code) >= 6:
            # Obtener los primeros 6 dígitos para buscar la Cuenta Detalle (nivel 4)
            prefix = code[:6]
            
            try:
                cuenta_detalle = CuentaDetalle.objects.get(code=prefix, level=4)
                cleaned_data['cuenta_detalle'] = cuenta_detalle
                
                # Heredar la naturaleza de la cuenta detalle
                cleaned_data['naturaleza'] = cuenta_detalle.naturaleza
                
                # También heredar si es cuenta fiscal
                cleaned_data['is_tax_account'] = cuenta_detalle.is_tax_account
                
            except CuentaDetalle.DoesNotExist:
                self.add_error('code', _('No existe una Cuenta Detalle (nivel 4) con el código: {}').format(prefix))
            except CuentaDetalle.MultipleObjectsReturned:
                self.add_error('code', _('Existen múltiples Cuentas Detalle con el código: {}').format(prefix))
        
        return cleaned_data

