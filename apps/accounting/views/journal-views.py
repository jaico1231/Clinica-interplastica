from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounting.models.journal import (
    AccountingPeriod, Journal, JournalEntry, JournalEntryLine
)
from apps.accounting.serializers.journal_serializers import (
    AccountingPeriodSerializer, JournalSerializer, 
    JournalEntrySerializer, JournalEntryDetailSerializer,
    JournalEntryLineSerializer
)
from apps.base.permissions import IsCompanyUser


class AccountingPeriodViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ver y editar períodos contables.
    """
    queryset = AccountingPeriod.objects.all()
    serializer_class = AccountingPeriodSerializer
    permission_classes = [IsAuthenticated, IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'fiscal_year', 'is_closed']
    search_fields = ['name']
    ordering_fields = ['start_date', 'end_date', 'fiscal_year', 'name']
    ordering = ['-start_date']
    
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
    
    @action(detail=True, methods=['post'])
    def close_period(self, request, pk=None):
        """
        Cierra un período contable.
        """
        period = self.get_object()
        
        # Verificar que todos los asientos estén balanceados
        unbalanced_entries = JournalEntry.objects.filter(
            accounting_period=period, 
            is_posted=False
        )
        
        if unbalanced_entries.exists():
            return Response(
                {"error": "No se puede cerrar el período porque existen asientos no contabilizados"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        period.is_closed = True
        period.save()
        
        serializer = self.get_serializer(period)
        return Response(serializer.data)


class JournalViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ver y editar diarios contables.
    """
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    permission_classes = [IsAuthenticated, IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'type']
    search_fields = ['name', 'code', 'prefix']
    ordering_fields = ['code', 'name', 'type']
    ordering = ['code']
    
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


class JournalEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ver y editar asientos contables.
    """
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    permission_classes = [IsAuthenticated, IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'journal', 'accounting_period', 'is_posted', 'is_reconciled', 'date']
    search_fields = ['reference', 'description', 'third_party__name']
    ordering_fields = ['date', 'reference', 'journal__name']
    ordering = ['-date', 'reference']
    
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
    
    def get_serializer_class(self):
        """
        Retorna diferentes serializadores dependiendo de la acción.
        """
        if self.action == 'retrieve':
            return JournalEntryDetailSerializer
        return JournalEntrySerializer
    
    @action(detail=True, methods=['post'])
    def post_entry(self, request, pk=None):
        """
        Contabiliza un asiento.
        """
        entry = self.get_object()
        
        # Verificar que el asiento esté balanceado
        if not entry.is_balanced():
            return Response(
                {"error": "El asiento no está balanceado"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que el período no esté cerrado
        if entry.accounting_period.is_closed:
            return Response(
                {"error": "No se puede contabilizar un asiento en un período cerrado"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entry.is_posted = True
        entry.save()
        
        serializer = self.get_serializer(entry)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reconcile(self, request, pk=None):
        """
        Concilia un asiento.
        """
        entry = self.get_object()
        
        # Verificar que el asiento esté contabilizado
        if not entry.is_posted:
            return Response(
                {"error": "El asiento debe estar contabilizado antes de conciliarse"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entry.is_reconciled = True
        entry.save()
        
        serializer = self.get_serializer(entry)
        return Response(serializer.data)


class JournalEntryLineViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ver y editar líneas de asiento contable.
    """
    queryset = JournalEntryLine.objects.all()
    serializer_class = JournalEntryLineSerializer
    permission_classes = [IsAuthenticated, IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['journal_entry', 'account', 'is_debit', 'third_party']
    search_fields = ['description', 'account__code', 'account__name']
    ordering_fields = ['journal_entry__date', 'journal_entry__reference', 'account__code']
    ordering = ['journal_entry__date', 'journal_entry__reference', 'id']
    
    def get_queryset(self):
        """
        Filtra el queryset según el asiento contable.
        """
        queryset = super().get_queryset()
        journal_entry_id = self.request.query_params.get('journal_entry')
        
        if journal_entry_id:
            queryset = queryset.filter(journal_entry_id=journal_entry_id)
            
        # Restricción adicional por compañía del usuario
        user = self.request.user
        if not user.is_superuser:
            user_companies = user.companies.all()
            queryset = queryset.filter(journal_entry__company__in=user_companies)
            
        return queryset
    
    def perform_create(self, serializer):
        """
        Al crear una línea, verificamos que el asiento no esté contabilizado.
        """
        journal_entry = serializer.validated_data['journal_entry']
        
        if journal_entry.is_posted:
            raise ValidationError(
                _("No se puede añadir líneas a un asiento contabilizado")
            )
            
        if journal_entry.accounting_period.is_closed:
            raise ValidationError(
                _("No se puede añadir líneas a un asiento en un período cerrado")
            )
        
        super().perform_create(serializer)
    
    def perform_update(self, serializer):
        """
        Al actualizar una línea, verificamos que el asiento no esté contabilizado.
        """
        journal_entry = serializer.instance.journal_entry
        
        if journal_entry.is_posted:
            raise ValidationError(
                _("No se puede modificar líneas de un asiento contabilizado")
            )
            
        if journal_entry.accounting_period.is_closed:
            raise ValidationError(
                _("No se puede modificar líneas de un asiento en un período cerrado")
            )
        
        super().perform_update(serializer)
    
    def perform_destroy(self, instance):
        """
        Al eliminar una línea, verificamos que el asiento no esté contabilizado.
        """
        journal_entry = instance.journal_entry
        
        if journal_entry.is_posted:
            raise ValidationError(
                _("No se puede eliminar líneas de un asiento contabilizado")
            )
            
        if journal_entry.accounting_period.is_closed:
            raise ValidationError(
                _("No se puede eliminar líneas de un asiento en un período cerrado")
            )
        
        super().perform_destroy(instance)