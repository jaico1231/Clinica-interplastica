# configUrls.py
from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.base.templatetags.menu_decorador import add_menu_name
from apps.accounting.views.PUCViews import (
    # Vistas de Naturaleza
    
    CuentaAuxiliarDeleteView,
    CuentaDetalleDeleteView,
    AllPucListView,
    SubcuentaCreateView,
    SubcuentaDeleteView,
    SubcuentaUpdateView,
    CuentaDetalleCreateView,
    CuentaDetalleUpdateView,
    CuentaAuxiliarCreateView,
    CuentaAuxiliarUpdateView
)

app_name = 'contabilidad'  # Define el nombre de la app para los templates y urls
app_icon= 'settings'

urlpatterns = [
    path(
        'puc/', 
         login_required(add_menu_name('PUC','manufacturing')(AllPucListView.as_view())), 
         name='puc_list'
         ),

    # Rutas para Subcuenta
    path('puc/subcuenta/nuevo/', 
        login_required(SubcuentaCreateView.as_view()), 
        name='subcuenta_create'),

    path('puc/subcuenta/editar/<int:pk>/', 
        login_required(SubcuentaUpdateView.as_view()), 
        name='subcuenta_edit'),
    
    path('puc/subcuenta/delete/<int:pk>/',
        login_required(SubcuentaDeleteView.as_view()), 
        name='subcuenta_delete'),
    
    # Rutas para Cuenta Detalle
    path('puc/cuentadetalle/nuevo/', 
        login_required(CuentaDetalleCreateView.as_view()), 
        name='cuentadetalle_create'),

    path('puc/cuentadetalle/editar/<int:pk>/', 
        login_required(CuentaDetalleUpdateView.as_view()), 
        name='cuentadetalle_edit'),
    
    path('puc/cuentadetalle/delete/<int:pk>/',
        login_required(CuentaDetalleDeleteView.as_view()), 
        name='cuentadetalle_delete'),
    
    # Rutas para Cuenta Auxiliar
    path('puc/cuentaauxiliar/nuevo/', 
        login_required(CuentaAuxiliarCreateView.as_view()), 
        name='cuentaauxiliar_create'),

    path('puc/cuentaauxiliar/editar/<int:pk>/', 
        login_required(CuentaAuxiliarUpdateView.as_view()), 
        name='cuentaauxiliar_edit'),

    path('puc/cuentaauxiliar/delete/<int:pk>/',
        login_required(CuentaAuxiliarDeleteView.as_view()), 
        name='cuentaauxiliar_delete'),
]