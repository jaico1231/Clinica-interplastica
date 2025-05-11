from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.accounting.models.tax import (
    TaxType, TaxRate, WithholdingTaxType, 
    WithholdingTaxConcept, CompanyTaxConfig
)
from apps.accounting.models.PUC import CuentaDetalle, CuentaAuxiliar
from apps.base.models.company import Company


class TaxTypeSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo TaxType
    """
    class Meta:
        model = TaxType
        fields = [
            'id', 'name', 'code', 'description', 'is_active',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class TaxRateSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo TaxRate
    """
    tax_type_name = serializers.StringRelatedField(source='tax_type', read_only=True)
    tax_account_name = serializers.StringRelatedField(source='tax_account', read_only=True)
    
    class Meta:
        model = TaxRate
        fields = [
            'id', 'tax_type', 'tax_type_name', 'name', 'code', 'rate',
            'description', 'is_default', 'valid_from', 'valid_to',
            'tax_account', 'tax_account_name', 'company', 'company_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'tax_type_name', 'tax_account_name']

    def validate(self, data):
        """
        Validar que las fechas sean correctas y que no haya conflictos con is_default
        """
        # Validar que valid_from sea anterior a valid_to
        if 'valid_from' in data and 'valid_to' in data and data['valid_from'] and data['valid_to']:
            if data['valid_from'] > data['valid_to']:
                raise serializers.ValidationError(
                    {'valid_to': _("La fecha de fin debe ser posterior a la fecha de inicio")}
                )

        # Validar is_default
        if data.get('is_default', False):
            tax_type = data.get('tax_type')
            instance = self.instance
            company = data.get('company')
            
            if instance:
                # Si estamos actualizando y no cambió el tax_type, no hay problema
                if instance.tax_type == tax_type and instance.company == company:
                    return data
                    
            # Comprobar si ya existe una tasa predeterminada para este tipo de impuesto y compañía
            if TaxRate.objects.filter(
                tax_type=tax_type,
                company=company,
                is_default=True
            ).exists():
                raise serializers.ValidationError(
                    {'is_default': _("Ya existe una tasa predeterminada para este tipo de impuesto y compañía")}
                )
        
        return data


class WithholdingTaxTypeSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo WithholdingTaxType
    """
    class Meta:
        model = WithholdingTaxType
        fields = [
            'id', 'name', 'code', 'description', 'is_active',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class WithholdingTaxConceptSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo WithholdingTaxConcept
    """
    withholding_type_name = serializers.StringRelatedField(source='withholding_type', read_only=True)
    tax_account_name = serializers.StringRelatedField(source='tax_account', read_only=True)
    
    class Meta:
        model = WithholdingTaxConcept
        fields = [
            'id', 'withholding_type', 'withholding_type_name', 'name', 'code',
            'rate', 'min_base', 'tax_account', 'tax_account_name',
            'description', 'valid_from', 'valid_to', 'company', 'company_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'withholding_type_name', 'tax_account_name'
        ]
        
    def validate(self, data):
        """
        Validar que las fechas sean correctas
        """
        # Validar que valid_from sea anterior a valid_to
        if 'valid_from' in data and 'valid_to' in data and data['valid_from'] and data['valid_to']:
            if data['valid_from'] > data['valid_to']:
                raise serializers.ValidationError(
                    {'valid_to': _("La fecha de fin debe ser posterior a la fecha de inicio")}
                )
        return data


class CompanyTaxConfigSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo CompanyTaxConfig
    """
    company_name = serializers.StringRelatedField(source='company', read_only=True)
    tax_rate_name = serializers.StringRelatedField(source='tax_rate', read_only=True)
    withholding_concept_name = serializers.StringRelatedField(source='withholding_concept', read_only=True)
    custom_account_name = serializers.StringRelatedField(source='custom_account', read_only=True)
    
    class Meta:
        model = CompanyTaxConfig
        fields = [
            'id', 'company', 'company_name', 'tax_rate', 'tax_rate_name',
            'withholding_concept', 'withholding_concept_name', 'is_active',
            'custom_rate', 'custom_account', 'custom_account_name', 'applied_to',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'company_name', 'tax_rate_name', 'withholding_concept_name', 'custom_account_name'
        ]
        
    def validate(self, data):
        """
        Validar que se proporcione exactamente uno de tax_rate o withholding_concept
        """
        tax_rate = data.get('tax_rate')
        withholding_concept = data.get('withholding_concept')
        
        if not tax_rate and not withholding_concept:
            raise serializers.ValidationError(
                _("Debe especificar una tasa de impuesto o un concepto de retención")
            )
            
        if tax_rate and withholding_concept:
            raise serializers.ValidationError(
                _("No puede especificar ambos: tasa de impuesto y concepto de retención")
            )
            
        return data