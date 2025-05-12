# configUrls.py
from django.urls import path
from apps.base.views.company import CompanyCreateView, CompanyUpdateView
from apps.base.views.genericcsvimportview import GenericCSVImportView
from apps.base.views.genericexportview import GenericExportView
from apps.base.views.genericviews import LoadCitiesView, LoadStatesView 
from apps.base.views.userview import ChangePasswordView, ToggleUserStatusView, UserCreateView, UserDeleteView, UserListView, UserUpdateView
from django.contrib.auth.decorators import login_required
from apps.base.templatetags.menu_decorador import add_menu_name
from apps.base.views.menuview import ListMenuView, MenuCreateView, MenuUpdateView, MenuItemListView, MenuItemCreateView, MenuItemUpdateView
from apps.base.views.groupsviews import GroupCreateView, GroupDeleteView, GroupListView, GroupUpdateView
from apps.base.views.genericToggleIs_active import GenericToggleActiveStatusView

app_name = 'configuracion'  # Define el nombre de la app para los templates y urls
app_icon= 'settings'
urlpatterns = [
    
    # path('dashboard/', LayoutView.as_view(template_name='dashboard.html'), name='dashboard'),
    # path('base/', LayoutView.as_view(template_name='tables/datatables.html'), name='base'),
    
    # Rutas para selectores dependientes
    path('ajax/load-states/', LoadStatesView.as_view(), name='ajax-load-states'),
    path('ajax/load-cities/', LoadCitiesView.as_view(), name='ajax-load-cities'),

    path('users/', login_required(add_menu_name('USUARIOS','person')(UserListView.as_view())), name='users_list'),    
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('users/<int:pk>/password/', ChangePasswordView.as_view(), name='change_password'),

    # Urls para creacion de grupos organizar las vistas para grupos
    path('groups/', login_required(add_menu_name('GRUPOS','groups')(GroupListView.as_view())), name='groups_list'),
    path('groups/create/', GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/update/', GroupUpdateView.as_view(), name='group_update'),
    path('groups/<int:pk>/delete/', GroupDeleteView.as_view(), name='group_delete'),

    path('menu/', login_required(add_menu_name('MENU','lists')(ListMenuView.as_view())), name='menu'),
    # path('menu/toggle/<int:pk>', login_required(ToggleMenuEstadoView.as_view()), name='togglemenu'),
    path('menu/create/', login_required(MenuCreateView.as_view()), name='menu_create'),
    path('menu/<int:pk>/edit/', login_required(MenuUpdateView.as_view()), name='menu_edit'),
    
    path('menuitems/', login_required(add_menu_name('MENU_ITEMS','lists')(MenuItemListView.as_view())), name='menu_items'),
    # path('menuitems/<int:pk>/toggle/', login_required(ToggleMenuItelEstadoView.as_view()), name='togglemenuitem'),
    path('menuitems/create/', login_required(MenuItemCreateView.as_view()), name='menuitem_create'),
    path('menuitems/<int:pk>/edit/', login_required(MenuItemUpdateView.as_view()), name='menuitem_edit'),

    path('company/int:pk',login_required(add_menu_name('EMPRESA','location_city')(CompanyUpdateView.as_view())), name='company_update'),
    path('company/areas/', login_required(add_menu_name('AREAS','location_city')(.as_view())), name='company_create'),
    path('toggle-status/<str:app_name>/<str:model_name>/<int:pk>/', GenericToggleActiveStatusView.as_view(), name='toggle_active_status'),
    

    
]