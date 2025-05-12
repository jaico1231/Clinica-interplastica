"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.base.urls.authUrls')),
    path('', include('apps.base.urls.configUrls')),
    path('', include('apps.third_party.urls')),
    path('', include('apps.accounting.urls.PUCUrls')),
    path('', include('apps.dashboard.urls.dashboardUrls')),
    path('', include('apps.notifications.urls')),
    path('', include('apps.audit.urls.auditUrls')),
    path('', include('apps.surveys.urls.surveyUrls')),
    path('', include('apps.waste.urls.WasteUrls')),
]
