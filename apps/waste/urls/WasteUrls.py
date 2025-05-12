from django.urls import path
from apps.base.templatetags.menu_decorador import add_menu_name
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _

from apps.waste.views.wastemanager_view import WasteManagerCreateView, WasteManagerDeleteView, WasteManagerDetailView, WasteManagerListView, WasteManagerUpdateView
from apps.waste.views.wasterecord_view import (
    WasteRecordCreateView, 
    WasteRecordDeleteView, 
    WasteRecordExportView, 
    WasteRecordListView, 
    WasteRecordUpdateView
    )
# from apps.waste.views.wasterecord_view import WasteManagerListView

app_name = 'control residuos'
app_icon = 'checklist'
urlpatterns = [
    # Waste Management URLs
    # path('waste-managers/', login_required(add_menu_name('LISTAR EMPRESAS DE GESTIÓN DE RESIDUOS', 'checklist')(WasteManagerListView.as_view())), name='waste_manager_list'),
    # path('waste-managers/create/', WasteManagerCreateView.as_view(), name='waste_create'),
    # path('waste-managers/<int:pk>/', WasteManagerDetailView.as_view(), name='waste_detail'),
    # path('waste-managers/<int:pk>/update/', WasteManagerUpdateView.as_view(), name='waste_update'),
    # path('waste-managers/<int:pk>/delete/', WasteManagerDeleteView.as_view(), name='waste_delete'),

    #Waste Redcord URLs
    path('waste-records/', login_required(add_menu_name(_('HISTORIAL CONTROL RESIDUOS'), 'checklist')(WasteRecordListView.as_view())), name='waste_record_list'),
    path('waste-records/create/', login_required(add_menu_name(_('CONTROL DIARIO'), 'delete')(WasteRecordCreateView.as_view())), name='waste_record_create'),
    path('waste-records/<int:pk>/update/', WasteRecordUpdateView.as_view(), name='waste_record_update'),
    path('waste-records/<int:pk>/delete/', WasteRecordDeleteView.as_view(), name='waste_record_delete'),
    path('waste/export/', WasteRecordExportView.as_view(), name='waste_record_export'),
]