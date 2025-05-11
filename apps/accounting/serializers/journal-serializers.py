from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounting.models.journal import (
    AccountingPeriod, Journal, JournalEntry, JournalEntryLine
)
from apps.accounting.models.PUC import CuentaAuxiliar
from apps.base.models.company import Company
from apps.third_party.models.third_party import ThirdParty


class AccountingPeriodSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo AccountingPeriod
    """
    company_name = serializers.StringRelatedField(source='company', read_only=True)
    
    class Meta:
        model = AccountingPeriod
        fields = [
            'id', 'company', 'company_name', 'name', 'start_date', 'end_date',
            'is_closed', 'fiscal_year', 'created_at', 'updated_at', 
            'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
        
    def validate(self, data):
        """
        Validaciones especiales para períodos contables
        """
        # Validar año fiscal vs fecha de inicio
        if 'start_date' in data and 'fiscal_year' in data:
            if data['start_date'].year != data['fiscal_year']:
                raise serializers.ValidationError(
                    {'fiscal_year': _('El año fiscal debe coincidir con el año de la fecha de inicio')}
                )
        
        # Validar que fecha fin sea posterior a fecha inicio
        if 'start_date' in data and 'end_date' in data:
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError(
                    {'end_date': _('La fecha de cierre debe ser posterior a la fecha de inicio')}
                )
        
        # Validar solapamiento con otros períodos
        instance = self.instance
        company = data.get('company', instance and instance.company)
        start_date = data.get('start_date', instance and instance.start_date)
        end_date = data.get('end_date', instance and instance.end_date)
        
        if company and start_date and end_date:
            overlapping = AccountingPeriod.objects.filter(
                company=company,
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            if instance:
                overlapping = overlapping.exclude(pk=instance.pk)
                
            if overlapping.exists():
                raise serializers.ValidationError(
                    _('Este periodo se solapa con otros periodos existentes')
                )
        
        return data


class JournalSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Journal
    """
    company_name = serializers.StringRelatedField(source='company', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Journal
        fields = [
            'id', 'company', 'company_name', 'code', 'name', 'type', 'type_display',
            'consecutive', 'prefix', 'resolution_number', 'resolution_date',
            'valid_from', 'valid_to', 'created_at', 'updated_at', 
            'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'consecutive']
        
    def validate(self, data):
        """
        Validar que las fechas sean correctas
        """
        if 'valid_from' in data and 'valid_to' in data and data['valid_to']:
            if data['valid_to'] <= data['valid_from']:
                raise serializers.ValidationError(
                    {'valid_to': _('La fecha de fin de validez debe ser posterior a la fecha de inicio')}
                )
        return data


class JournalEntryLineSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo JournalEntryLine
    """
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    third_party_name = serializers.StringRelatedField(source='third_party', read_only=True)
    tax_rate_name = serializers.StringRelatedField(source='tax_rate', read_only=True)
    withholding_concept_name = serializers.StringRelatedField(source='withholding_concept', read_only=True)
    
    class Meta:
        model = JournalEntryLine
        fields = [
            'id', 'journal_entry', 'account', 'account_code', 'account_name',
            'description', 'is_debit', 'amount', 'third_party', 'third_party_name',
            'tax_base', 'tax_rate', 'tax_rate_name', 'withholding_concept',
            'withholding_concept_name', 'created_at', 'updated_at', 
            'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
        
    def validate(self, data):
        """
        Validaciones específicas para líneas de asiento
        """
        # Validar que la cuenta permita movimientos
        account = data.get('account')
        if account and not account.allows_movements:
            raise serializers.ValidationError(
                {'account': _('Esta cuenta no permite movimientos directos')}
            )
        
        # Validar coherencia de impuestos
        tax_rate = data.get('tax_rate')
        withholding_concept = data.get('withholding_concept')
        
        if tax_rate and withholding_concept:
            raise serializers.ValidationError(
                _("No puede especificar ambos: tasa de impuesto y concepto de retención")
            )
        
        tax_base = data.get('tax_base', 0)
        if (tax_rate or withholding_concept) and tax_base <= 0:
            raise serializers.ValidationError(
                {'tax_base': _('La base gravable debe ser mayor que cero si se especifica un impuesto')}
            )
        
        # Validar que el asiento no esté contabilizado o en un período cerrado
        journal_entry = data.get('journal_entry')
        if journal_entry:
            if journal_entry.is_posted:
                raise serializers.ValidationError(
                    _("No se puede modificar un asiento contabilizado")
                )
            
            if journal_entry.accounting_period.is_closed:
                raise serializers.ValidationError(
                    _("No se puede modificar un asiento en un período cerrado")
                )
                
        return data


class JournalEntrySerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo JournalEntry (versión básica)
    """
    company_name = serializers.StringRelatedField(source='company', read_only=True)
    journal_name = serializers.StringRelatedField(source='journal', read_only=True)
    period_name = serializers.StringRelatedField(source='accounting_period', read_only=True)
    third_party_name = serializers.StringRelatedField(source='third_party', read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)
    total_debits = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_credits = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    
    class Meta:
        model = JournalEntry
        fields = [
            'id', 'company', 'company_name', 'journal', 'journal_name',
            'accounting_period', 'period_name', 'reference', 'date',
            'description', 'third_party', 'third_party_name',
            'is_posted', 'is_reconciled', 'is_balanced',
            'total_debits', 'total_credits', 'created_at', 'updated_at', 
            'created_by', 'updated_by'
        ]
        read_only_fields = [
            'reference', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'is_balanced', 'total_debits', 'total_credits'
        ]
        
    def validate(self, data):
        """
        Validar que la fecha esté dentro del período y que el período no esté cerrado
        """
        # Validar que la fecha está dentro del período contable
        date = data.get('date')
        accounting_period = data.get('accounting_period')
        
        if date and accounting_period:
            if date < accounting_period.start_date or date > accounting_period.end_date:
                raise serializers.ValidationError(
                    {'date': _("La fecha del asiento debe estar dentro del período contable seleccionado")}
                )
        
        # Validar que el período no esté cerrado
        if accounting_period and accounting_period.is_closed:
            raise serializers.ValidationError(
                {'accounting_period': _("No se puede crear o modificar un asiento en un período cerrado")}
            )
        
        # Si estamos actualizando, validar que no esté contabilizado
        instance = self.instance
        if instance and instance.is_posted:
            raise serializers.ValidationError(
                _("No se puede modificar un asiento contabilizado")
            )
        
        return data
    
    def to_representation(self, instance):
        """
        Añadir campos calculados
        """
        representation = super().to_representation(instance)
        representation['is_balanced'] = instance.is_balanced()
        representation['total_debits'] = instance.total_debits()
        representation['total_credits'] = instance.total_credits()
        return representation


class JournalEntryLineNestedSerializer(serializers.ModelSerializer):
    """
    Serializer para líneas de asiento anidadas
    """
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    third_party_name = serializers.StringRelatedField(source='third_party', read_only=True)
    tax_rate_name = serializers.StringRelatedField(source='tax_rate', read_only=True)
    withholding_concept_name = serializers.StringRelatedField(source='withholding_concept', read_only=True)
    
    class Meta:
        model = JournalEntryLine
        fields = [
            'id', 'account', 'account_code', 'account_name',
            'description', 'is_debit', 'amount', 'third_party', 'third_party_name',
            'tax_base', 'tax_rate', 'tax_rate_name', 'withholding_concept',
            'withholding_concept_name'
        ]


class JournalEntryDetailSerializer(JournalEntrySerializer):
    """
    Serializer para el modelo JournalEntry con sus líneas (detalle)
    """
    lines = JournalEntryLineNestedSerializer(many=True, read_only=True)
    
    class Meta(JournalEntrySerializer.Meta):
        fields = JournalEntrySerializer.Meta.fields + ['lines']
        
    @transaction.atomic
    def create(self, validated_data):
        lines_data = self.context['request'].data.get('lines', [])
        
        # Crear el asiento
        journal_entry = JournalEntry.objects.create(**validated_data)
        
        # Crear las líneas
        for line_data in lines_data:
            line_data['journal_entry'] = journal_entry.id
            line_serializer = JournalEntryLineSerializer(data=line_data)
            if line_serializer.is_valid(raise_exception=True):
                line_serializer.save()
        
        return journal_entry
    
    @transaction.atomic
    def update(self, instance, validated_data):
        lines_data = self.context['request'].data.get('lines', [])
        
        # Actualizar el asiento
        journal_entry = super().update(instance, validated_data)
        
        # Si se proporcionaron líneas, reemplazar todas
        if 'lines' in self.context['request'].data:
            # Eliminar líneas existentes
            instance.lines.all().delete()
            
            # Crear nuevas líneas
            for line_data in lines_data:
                line_data['journal_entry'] = journal_entry.id
                line_serializer = JournalEntryLineSerializer(data=line_data)
                if line_serializer.is_valid(raise_exception=True):
                    line_serializer.save()
        
        return journal_entry