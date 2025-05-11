from django.contrib import admin
from .models import (
    Naturaleza, 
    GrupoCuenta, 
    CuentaMayor, 
    SubCuenta, 
    SubCuenta,
    CuentaDetalle,
    CuentaAuxiliar,
    AccountingPeriod,
    Journal,
    JournalEntry,
    JournalEntryLine,
    TaxType,
    TaxRate,
    WithholdingTaxType,
    WithholdingTaxConcept,
    CompanyTaxConfig
    )

# Register your models here.

admin.site.register(Naturaleza)

admin.site.register(GrupoCuenta)

admin.site.register(CuentaMayor)

admin.site.register(SubCuenta)

admin.site.register(CuentaDetalle)

admin.site.register(CuentaAuxiliar)

admin.site.register(AccountingPeriod)

admin.site.register(Journal)

admin.site.register(JournalEntry)

admin.site.register(JournalEntryLine)

admin.site.register(TaxType)

admin.site.register(TaxRate)

admin.site.register(WithholdingTaxType)

admin.site.register(WithholdingTaxConcept)

admin.site.register(CompanyTaxConfig)

# Inicio de sesión para administradores

admin.site.site_header = "InnoSmart CRM"

admin.site.site_title = "InnoSmart CRM"

admin.site.index_title = "Panel de Administración"