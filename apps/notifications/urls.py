# notifications/urls.py

from django.urls import path

from apps.notifications.views.email_configure import (
    EmailConfigurationCreateView, 
    EmailConfigurationDeleteView, 
    EmailConfigurationListView, 
    EmailConfigurationUpdateView, 
    # SMSConfigurationCreateView, 
    # SMSConfigurationDeleteView, 
    # SMSConfigurationListView, 
    # SMSConfigurationUpdateView, 
    # WhatsAppConfigurationCreateView, 
    # WhatsAppConfigurationDeleteView, 
    # WhatsAppConfigurationListView, 
    # WhatsAppConfigurationUpdateView
    )

from apps.notifications.views.notifications_view import (
    send_email_via_backend,
    _send_smtp_email,
    _send_sendgrid_email,
    _send_console_email,
    send_sms_via_backend,
    _send_twilio_sms,
    _send_debug_sms,
    send_whatsapp_via_backend,
    _send_twilio_whatsapp,
    _send_debug_whatsapp,
)
from apps.notifications.views.sms_configure import (
    SMSConfigurationCreateView,
    SMSConfigurationDeleteView,
    SMSConfigurationListView,
    SMSConfigurationUpdateView,
    send_test_sms_view,
    )
from apps.notifications.views.test_email_view import test_email_view
from apps.notifications.views.whatssap_configure import (
    WhatsAppConfigurationListView,
    WhatsAppConfigurationCreateView,
    WhatsAppConfigurationUpdateView,
    WhatsAppConfigurationDeleteView
    )

app_name = 'notificaciones' # Namespace para las URLs
app_icon = 'send' # Icono para la app en el menú lateral

urlpatterns = [
    # Email Configuration URLs
    path('config/email/', EmailConfigurationListView.as_view(), name='email_config_list'),
    path('config/email/new/', EmailConfigurationCreateView.as_view(), name='email_config_create'),
    path('config/email/<int:pk>/edit/', EmailConfigurationUpdateView.as_view(), name='email_config_update'),
    path('config/email/<int:pk>/delete/', EmailConfigurationDeleteView.as_view(), name='email_config_delete'),
    path('config/email/test/', test_email_view, name='email_config_test'),  # URL para prueba de email
    
    # SMS Configuration URLs
    path('config/sms/', SMSConfigurationListView.as_view(), name='sms_config_list'),
    path('config/sms/new/', SMSConfigurationCreateView.as_view(), name='sms_config_create'),
    path('config/sms/<int:pk>/edit/', SMSConfigurationUpdateView.as_view(), name='sms_config_update'),
    path('config/sms/<int:pk>/delete/', SMSConfigurationDeleteView.as_view(), name='sms_config_delete'),
    path('config/sms/',send_test_sms_view, name='send_test_sms'),  # URL para prueba de SMS
    # WhatsApp Configuration URLs
    path('config/whatsapp/', WhatsAppConfigurationListView.as_view(), name='whatsapp_config_list'),
    path('config/whatsapp/new/', WhatsAppConfigurationCreateView.as_view(), name='whatsapp_config_create'),
    path('config/whatsapp/<int:pk>/edit/', WhatsAppConfigurationUpdateView.as_view(), name='whatsapp_config_update'),
    path('config/whatsapp/<int:pk>/delete/', WhatsAppConfigurationDeleteView.as_view(), name='whatsapp_config_delete'),

    # api de notificaciones
    path('send/email/', send_email_via_backend, name='send_email'),
    path('send/sms/', send_sms_via_backend, name='send_sms'),
    path('send/whatsapp/', send_whatsapp_via_backend, name='send_whatsapp'),
    
    # Agrega aquí otras URLs de la app (logs, templates, etc.) si es necesario
]