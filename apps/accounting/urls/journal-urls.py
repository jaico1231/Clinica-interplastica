from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounting.views.journal_views import (
    AccountingPeriodViewSet, JournalViewSet, 
    JournalEntryViewSet, JournalEntryLineViewSet
)

# Creamos un router y registramos nuestros viewsets
router = DefaultRouter()
router.register(r'accounting-periods', AccountingPeriodViewSet)
router.register(r'journals', JournalViewSet)
router.register(r'journal-entries', JournalEntryViewSet)
router.register(r'journal-entry-lines', JournalEntryLineViewSet)

# Patrones de URL para el sistema de diarios contables
urlpatterns = [
    path('', include(router.urls)),
]