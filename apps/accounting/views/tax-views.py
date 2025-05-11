from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounting.models.tax import (
    TaxType, TaxRate, WithholdingTaxType, 
    WithholdingTaxConcept, CompanyTaxConfig
)
from apps.accounting.serializers.tax_serializers import (
    TaxTypeSerializer, TaxRateSerializer, 
    WithholdingTaxTypeSerializer, WithholdingTaxConceptSerializer,
    CompanyTaxConfigSerializer
)
from apps.base.permissions import IsCompanyUser


class TaxTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ver y editar tipos de impuestos.
    """
    queryset = TaxType.objects.all()
    serializer_class = TaxTypeSerializer
    permission_classes = [IsAuthenticated, IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']


class TaxRateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ver y editar tasas de impuestos.
    """
    queryset = TaxRate.objects.all()
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticated, IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tax_type', 'is_default', 'company']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'tax_type__name', 'rate', 'created_at']
    ordering = ['tax_type__name', 'rate']
    
    def get_queryset(self):
        """
        Filtra el queryset según la compañía del usuario si se proporciona
        el parámetro company_id.
        """
        queryset = super().get_queryset()
        company_id = self.request.query_params.get('company_id')
        
        if company_id:
            queryset = queryset.filter(company_id=company_id)
            
        return queryset


class WithholdingTaxTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ver y editar tipos de retención.
    """
    queryset = WithholdingTaxType.objects.all()
    serializer_class = WithholdingTaxTypeSerializer
    permission_classes = [IsAuthenticated, IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']


class WithholdingTaxConceptViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ver y editar conceptos de retención.
    """
    queryset = WithholdingTaxConcept.objects.all()
    serializer_class = WithholdingTaxConceptSerializer
    permission_classes = [IsAuthenticated, IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['withholding_type', 'company']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'withholding_type__name', 'rate', 'created_at']
    ordering = ['withholding_type__name', 'name']
    
    def get_queryset(self):
        """
        Filtra el queryset según la compañía del usuario si se proporciona
        el parámetro company_id.
        """
        queryset = super().get_queryset()
        company_id = self.request.query_params.get('company_id')
        
        if company_id:
            queryset = queryset.filter(company_id=company_id)
            
        return queryset


class CompanyTaxConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ver y editar configuraciones de impuestos por empresa.
    """
    queryset = CompanyTaxConfig.objects.all()
    serializer_class = CompanyTaxConfigSerializer
    permission_classes = [IsAuthenticated, IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'tax_rate', 'withholding_concept', 'is_active', 'applied_to']
    search_fields = ['company__name', 'tax_rate__name', 'withholding_concept__name']
    ordering_fields = ['company__name', 'applied_to', 'created_at']
    ordering = ['company__name']
    
    def get_queryset(self):
        """
        Filtra el queryset según la compañía del usuario.
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_superuser:
            user_companies = user.companies.all()
            queryset = queryset.filter(company__in=user_companies)
            
        return queryset