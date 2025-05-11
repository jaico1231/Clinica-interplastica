from django import forms

from apps.base.models.company import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'
        widgets = {
            'country': forms.Select(attrs={'class': 'form-select select2'}),
            'state': forms.Select(attrs={'class': 'form-select select2', 'style': 'width: 100%;'}),
            'city': forms.Select(attrs={'class': 'form-select select2', 'style': 'width: 100%;'}),
            'document_type': forms.Select(attrs={'class': 'form-select select2', 'style': 'width: 100%;'}),
            'payment_periodicity': forms.Select(attrs={'class': 'form-select select2', 'style': 'width: 100%;'}),
            'account_type': forms.Select(attrs={'class': 'form-select select2', 'style': 'width: 100%;'}),
        }
        exclude = ['created_at', 'updated_at', 'deleted_at']

        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases CSS a todos los campos del formulario
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'form-control'
            elif field_name in ['country', 'state', 'city', 'document_type', 'payment_periodicity', 'account_type']:
                # Aplicar select2 con configuración específica para estos campos
                field.widget.attrs['class'] = 'form-select select2'
                field.widget.attrs['style'] = 'width: 100%;'  # Forzar ancho al 100%
            else:
                field.widget.attrs['class'] = 'form-control'
                
            # Asegurar que los campos no requeridos estén claramente marcados
            if not field.required:
                if field.label:
                    field.label += ' (Opcional)'