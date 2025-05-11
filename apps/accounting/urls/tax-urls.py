from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounting.views.tax_views import (
    TaxTypeViewSet, TaxRateViewSet, WithholdingTaxTypeViewSet,
    WithholdingTaxConceptViewSet, CompanyTaxConfigViewSet
)

# Creamos un router y registramos nuestros viewsets
router = DefaultRouter()
router.register(r'tax-types', TaxTypeViewSet)
router.register(r'tax-rates', TaxRateViewSet)
router.register(r'withholding-types', WithholdingTaxTypeViewSet)
router.register(r'withholding-concepts', WithholdingTaxConceptViewSet)
router.register(r'company-tax-configs', CompanyTaxConfigViewSet)

# Patrones de URL para impuestos
urlpatterns = [
    path('', include(router.urls)),
]