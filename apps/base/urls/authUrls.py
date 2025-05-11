# authUrls.py
from django.urls import path
from django.views.decorators.cache import never_cache
from apps.base.views.loginview import CustomLoginView, logout_view
from django.contrib.auth.decorators import login_required
from apps.base.templatetags.menu_decorador import add_menu_name

app_name = 'auth'  # Define el nombre de la app para los templates y urls
icon = 'configure' 
urlpatterns = [
    path('login/', never_cache(CustomLoginView.as_view()), name='login'),
    path('logout/', logout_view, name='logout'),
    
]