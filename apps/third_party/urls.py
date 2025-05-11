from django.urls import path
from apps.base.templatetags.menu_decorador import add_menu_name
from django.contrib.auth.decorators import login_required
from apps.third_party.views.third_partyview import ThirdPartyCreateView, ThirdPartyDeleteView, ThirdPartyExportView, ThirdPartyImportView, ThirdPartyListView, ThirdPartyUpdateView, ToggleThirdPartyStatusView


app_name = 'administracion terceros'
app_icon = 'supervisor_account'
urlpatterns = [
    # Rutas para ThirdParty
    path('third-parties/', login_required(add_menu_name('TERCEROS','supervisor_account')(ThirdPartyListView.as_view())), name='third-party-list'),
    path('third-parties/create/', ThirdPartyCreateView.as_view(), name='third-party_create'),
    path('third-parties/<int:pk>/update/', ThirdPartyUpdateView.as_view(), name='third-party_update'),
    path('third-parties/<int:pk>/delete/', ThirdPartyDeleteView.as_view(), name='third-party_delete'),
    path('third-parties/<int:pk>/toggle-status/', ToggleThirdPartyStatusView.as_view(), name='third-party-toggle_status'),
    path('third-parties/upload/', ThirdPartyImportView.as_view(), name='third-party-upload'),       
    path('third-parties/export/', ThirdPartyExportView.as_view(), name='third-party-download'),
]
# path('groups/', login_required(add_menu_name('GRUPOS','groups')(GenericListView.as_view(model=Group, template_name='groups/list.html'))), name='groups_list'),