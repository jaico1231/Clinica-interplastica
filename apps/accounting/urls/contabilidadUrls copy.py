# # configUrls.py
# from django.urls import path
# from django.contrib.auth.decorators import login_required
# from apps.base.templatetags.menu_decorador import add_menu_name
# from apps.accounting.views.PUCViews import (
#     # Vistas de Naturaleza
#     NaturalezaListView,
#     NaturalezaCreateView,
#     NaturalezaUpdateView,
#     NaturalezaDeleteView,
#     NaturalezaDetailView,
    
#     # Vistas de GrupoCuenta
#     GrupoCuentaListView,
#     GrupoCuentaCreateView,
#     GrupoCuentaUpdateView,
#     GrupoCuentaDeleteView,
#     GrupoCuentaDetailView,
    
#     # Vistas de CuentaMayor
#     CuentaMayorListView,
#     CuentaMayorCreateView,
#     CuentaMayorUpdateView,
#     CuentaMayorDeleteView,
#     CuentaMayorDetailView,
#     PUCStructureListView,
    
#     # Vistas de SubCuenta
#     SubCuentaListView,
#     SubCuentaCreateView,
#     SubCuentaUpdateView,
#     SubCuentaDeleteView,
#     SubCuentaDetailView,
    
#     # Vistas de CuentaDetalle
#     CuentaDetalleListView,
#     CuentaDetalleCreateView,
#     CuentaDetalleUpdateView,
#     CuentaDetalleDeleteView,
#     CuentaDetalleDetailView,
    
#     # Vistas de CuentaAuxiliar
#     CuentaAuxiliarListView,
#     CuentaAuxiliarCreateView,
#     CuentaAuxiliarUpdateView,
#     CuentaAuxiliarDeleteView,
#     CuentaAuxiliarDetailView,
# )
# app_name = 'configuracion'  # Define el nombre de la app para los templates y urls
# app_icon= 'settings'
# urlpatterns = [
#     path('puc/', PUCStructureListView.as_view(), name='puc-structure-list'),
#     # URLs para Naturaleza
#     path('naturalezas/', NaturalezaListView.as_view(), name='naturaleza_list'),
#     path('naturalezas/create/', NaturalezaCreateView.as_view(), name='naturaleza_create'),
#     path('naturalezas/<int:pk>/', NaturalezaDetailView.as_view(), name='naturaleza_detail'),
#     path('naturalezas/<int:pk>/update/', NaturalezaUpdateView.as_view(), name='naturaleza_update'),
#     path('naturalezas/<int:pk>/delete/', NaturalezaDeleteView.as_view(), name='naturaleza_delete'),
    
#     # URLs para GrupoCuenta
#     path('grupos-cuenta/', GrupoCuentaListView.as_view(), name='grupocuenta_list'),
#     path('grupos-cuenta/create/', GrupoCuentaCreateView.as_view(), name='grupocuenta_create'),
#     path('grupos-cuenta/<int:pk>/', GrupoCuentaDetailView.as_view(), name='grupocuenta_detail'),
#     path('grupos-cuenta/<int:pk>/update/', GrupoCuentaUpdateView.as_view(), name='grupocuenta_update'),
#     path('grupos-cuenta/<int:pk>/delete/', GrupoCuentaDeleteView.as_view(), name='grupocuenta_delete'),
    
#     # URLs para CuentaMayor
#     path('cuentas-mayor/', CuentaMayorListView.as_view(), name='cuentamayor_list'),
#     path('cuentas-mayor/create/', CuentaMayorCreateView.as_view(), name='cuentamayor_create'),
#     path('cuentas-mayor/<int:pk>/', CuentaMayorDetailView.as_view(), name='cuentamayor_detail'),
#     path('cuentas-mayor/<int:pk>/update/', CuentaMayorUpdateView.as_view(), name='cuentamayor_update'),
#     path('cuentas-mayor/<int:pk>/delete/', CuentaMayorDeleteView.as_view(), name='cuentamayor_delete'),
    
#     # URLs para SubCuenta
#     path('subcuentas/', SubCuentaListView.as_view(), name='subcuenta_list'),
#     path('subcuentas/create/', SubCuentaCreateView.as_view(), name='subcuenta_create'),
#     path('subcuentas/<int:pk>/', SubCuentaDetailView.as_view(), name='subcuenta_detail'),
#     path('subcuentas/<int:pk>/update/', SubCuentaUpdateView.as_view(), name='subcuenta_update'),
#     path('subcuentas/<int:pk>/delete/', SubCuentaDeleteView.as_view(), name='subcuenta_delete'),
    
#     # URLs para CuentaDetalle
#     path('cuentas-detalle/', CuentaDetalleListView.as_view(), name='cuentadetalle_list'),
#     path('cuentas-detalle/create/', CuentaDetalleCreateView.as_view(), name='cuentadetalle_create'),
#     path('cuentas-detalle/<int:pk>/', CuentaDetalleDetailView.as_view(), name='cuentadetalle_detail'),
#     path('cuentas-detalle/<int:pk>/update/', CuentaDetalleUpdateView.as_view(), name='cuentadetalle_update'),
#     path('cuentas-detalle/<int:pk>/delete/', CuentaDetalleDeleteView.as_view(), name='cuentadetalle_delete'),
    
#     # URLs para CuentaAuxiliar
#     path('cuentas-auxiliares/', CuentaAuxiliarListView.as_view(), name='cuentaauxiliar_list'),
#     path('cuentas-auxiliares/create/', CuentaAuxiliarCreateView.as_view(), name='cuentaauxiliar_create'),
#     path('cuentas-auxiliares/<int:pk>/', CuentaAuxiliarDetailView.as_view(), name='cuentaauxiliar_detail'),
#     path('cuentas-auxiliares/<int:pk>/update/', CuentaAuxiliarUpdateView.as_view(), name='cuentaauxiliar_update'),
#     path('cuentas-auxiliares/<int:pk>/delete/', CuentaAuxiliarDeleteView.as_view(), name='cuentaauxiliar_delete'),

    
# ]