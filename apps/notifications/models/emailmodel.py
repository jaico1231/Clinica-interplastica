from datetime import timezone
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_cryptography.fields import encrypt
from apps.base.models.basemodel import BaseModel
import logging

logger = logging.getLogger(__name__)

class EmailConfiguration(BaseModel):
    class EmailBackend(models.TextChoices):
        SMTP = 'SMTP', _('SMTP Standard')
        SENDGRID = 'SENDGRID', _('SendGrid API')
        SES = 'SES', _('Amazon SES')
        CONSOLE = 'console', _('Console Debug')
        FILE = 'file', _('File Debug')
    
    class SecurityProtocol(models.TextChoices):
        NONE = 'none', _('None')
        TLS = 'TLS', _('TLS')
        SSL = 'SSL', _('SSL')
        STARTTLS = 'STARTTLS', _('STARTTLS')

    name = models.CharField(
        _("Configuration Name"),
        max_length=100,
        unique=True,
        help_text=_("Descriptive name for this configuration")
    )
    
    backend = models.CharField(
        _("Email Backend"),
        max_length=20,
        choices=EmailBackend.choices,
        default=EmailBackend.SMTP
    )
    
    host = models.CharField(
        _("Server Host"),
        max_length=255,
        blank=True,
        null=True
    )
    
    port = models.PositiveIntegerField(
        _("Port Number"),
        blank=True,
        null=True,
        help_text=_("Default ports: SMTP (25, 587), SSL (465), SendGrid (443)")
    )
    
    username = models.CharField(
        _("Authentication Username"),
        max_length=255,
        blank=True,
        null=True
    )
    
    password = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    
    api_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("For API-based services like SendGrid")
    )
    
    security_protocol = models.CharField(
        _("Security Protocol"),
        max_length=20,
        choices=SecurityProtocol.choices,
        default=SecurityProtocol.TLS
    )
    
    timeout = models.PositiveIntegerField(
        _("Connection Timeout"),
        default=10,
        help_text=_("Timeout in seconds for connection attempts")
    )
    
    from_email = models.EmailField(
        _("Default From Address"),
        max_length=255,
        help_text=_("Format: 'Name <email@example.com>'")
    )
    
    is_active = models.BooleanField(
        _("Active Configuration"),
        default=False,
        help_text=_("Only one configuration can be active at a time")
    )
    
    use_custom_headers = models.BooleanField(
        _("Use Custom Headers"),
        default=False
    )
    
    custom_headers = models.JSONField(
        _("Custom Email Headers"),
        blank=True,
        null=True,
        help_text=_("JSON format for additional headers")
    )
    
    fail_silently = models.BooleanField(
        _("Fail Silently"),
        default=False,
        help_text=_("Set to True to suppress exceptions")
    )
    
    class Meta:
        verbose_name = _("Email Configuration")
        verbose_name_plural = _("Email Configurations")
        ordering = ['-is_active', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_configuration'
            )
        ]

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
    
    def clean(self):
        """
        Validación personalizada para diferentes backends
        """
        super().clean()
        
        # Validación especifica según el backend
        if self.backend == self.EmailBackend.SMTP:
            if not self.host:
                raise ValidationError({'host': _("Host server is required for SMTP")})
            if not self.port:
                raise ValidationError({'port': _("Port is required for SMTP")})
            if not self.username and not self.backend == self.EmailBackend.CONSOLE:
                raise ValidationError({'username': _("Username is required for SMTP authentication")})
            if not self.password and not self.backend == self.EmailBackend.CONSOLE:
                raise ValidationError({'password': _("Password is required for SMTP authentication")})
        
        elif self.backend == self.EmailBackend.SENDGRID:
            if not self.api_key:
                raise ValidationError({'api_key': _("API Key is required for SendGrid")})
        
        elif self.backend == self.EmailBackend.SES:
            if not self.username:  # AWS Access Key
                raise ValidationError({'username': _("AWS Access Key is required for Amazon SES")})
            if not self.password:  # AWS Secret Key
                raise ValidationError({'password': _("AWS Secret Key is required for Amazon SES")})
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para gestionar la configuración activa
        """
        # Si esta configuración está activa, desactivar todas las demás
        if self.is_active:
            EmailConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        
        # Si no hay contraseña o API key y es una actualización, mantener los valores existentes
        if self.pk:
            try:
                old_instance = EmailConfiguration.objects.get(pk=self.pk)
                if not self.password and old_instance.password:
                    self.password = old_instance.password
                if not self.api_key and old_instance.api_key:
                    self.api_key = old_instance.api_key
            except EmailConfiguration.DoesNotExist:
                pass
                
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_configuration(cls):
        """
        Obtiene la configuración activa del sistema
        
        Returns:
            EmailConfiguration: Instancia activa o None si no hay ninguna
        """
        try:
            return cls.objects.filter(is_active=True).first()
        except Exception as e:
            logger.error(f"Error al obtener configuración de email activa: {e}")
            return None
    
    @property
    def connection_params(self):
        """
        Devuelve los parámetros de conexión según el backend seleccionado
        
        Returns:
            dict: Parámetros de conexión para el backend correspondiente
        """
        params = {}
        
        # Parámetros comunes
        if self.timeout:
            params['timeout'] = self.timeout
        
        # SMTP Backend
        if self.backend == self.EmailBackend.SMTP:
            params['host'] = self.host
            params['port'] = self.port
            
            # Solo incluir username y password si están configurados
            if self.username:
                params['username'] = self.username
            
            # Verificar que la contraseña esté configurada para conexiones SMTP
            if self.password:
                params['password'] = self.password
            else:
                logger.warning(f"⚠️ Configuración SMTP '{self.name}' (ID: {self.pk}) no tiene contraseña configurada")
                logger.warning(f"La conexión a servidores SMTP como {self.host} puede fallar sin autenticación")
            
            # Configuración SSL/TLS
            params['use_tls'] = self.security_protocol in [
                self.SecurityProtocol.TLS, 
                self.SecurityProtocol.STARTTLS
            ]
            params['use_ssl'] = self.security_protocol == self.SecurityProtocol.SSL
        
        # SendGrid Backend
        elif self.backend == self.EmailBackend.SENDGRID:
            # Para SendGrid, necesitamos API key
            if self.api_key:
                params['api_key'] = self.api_key
            else:
                logger.warning(f"Configuración SendGrid '{self.name}' (ID: {self.pk}) no tiene API key configurada")
        
        # Amazon SES Backend
        elif self.backend == self.EmailBackend.SES:
            # AWS requiere credenciales
            params['region'] = getattr(self, 'region', 'us-east-1')  # Usar valor por defecto si no existe
            params['aws_access_key_id'] = self.username
            params['aws_secret_access_key'] = self.password or self.api_key
        
        # Console o File Backend
        elif self.backend == self.EmailBackend.CONSOLE:
            # No requiere parámetros adicionales
            pass
        elif self.backend == self.EmailBackend.FILE:
            from django.conf import settings
            params['file_path'] = getattr(settings, 'EMAIL_FILE_PATH', None)
        
        return params
    
    def test_connection(self, test_recipient=None):
        """
        Prueba la conexión con esta configuración
        
        Args:
            test_recipient (str, optional): Dirección de correo para prueba
            
        Returns:
            tuple: (bool, str) - (éxito, mensaje)
        """
        from django.core.mail import EmailMessage
        from django.core.mail import get_connection as get_email_connection
        
        if not test_recipient:
            test_recipient = self.from_email
        
        try:
            # Configurar backend y conexión según el tipo
            backend_path = 'django.core.mail.backends.smtp.EmailBackend'  # Por defecto
            
            if self.backend == self.EmailBackend.SENDGRID:
                backend_path = 'django.core.mail.backends.smtp.EmailBackend'
            elif self.backend == self.EmailBackend.SES:
                backend_path = 'django_ses.SESBackend'
            elif self.backend == self.EmailBackend.CONSOLE:
                backend_path = 'django.core.mail.backends.console.EmailBackend'
            elif self.backend == self.EmailBackend.FILE:
                backend_path = 'django.core.mail.backends.filebased.EmailBackend'
            
            # Obtener los parámetros de conexión
            connection_params = self.connection_params
            
            # Imprimir información para depuración (ocultando datos sensibles)
            logger.info(f"Probando conexión para {self.name} ({self.backend})")
            debug_params = {k: '********' if k in ['password', 'api_key', 'aws_secret_access_key'] 
                           else v for k, v in connection_params.items()}
            logger.info(f"Parámetros: {debug_params}")
            
            # Crear conexión
            connection = get_email_connection(
                backend=backend_path,
                **connection_params
            )
            
            # Enviar correo de prueba
            email = EmailMessage(
                subject=f"Prueba de configuración - {self.name}",
                body=f"""Este es un correo de prueba enviado desde la configuración "{self.name}".
                
Si recibes este correo, la configuración funciona correctamente.""",
                from_email=self.from_email,
                to=[test_recipient],
                connection=connection
            )
            
            email.send(fail_silently=False)
            return True, f"Prueba enviada correctamente a {test_recipient}"
            
        except Exception as e:
            error_message = f"Error al probar la conexión: {str(e)}"
            logger.error(error_message)
            return False, error_message   
    
    

class SMSConfiguration(BaseModel):
    class SMSBackend(models.TextChoices):
        TWILIO = 'TWILIO', _('Twilio')
        AWS_SNS = 'AWS_SNS', _('AWS SNS')
        PLIVO = 'PLIVO', _('Plivo')
        NEXMO = 'NEXMO', _('Vonage (Nexmo)')
        DEBUG = 'DEBUG', _('Debug Console')
    
    name = models.CharField(
        _("Configuration Name"),
        max_length=100,
        unique=True,
        help_text=_("Descriptive name for this configuration")
    )
    
    backend = models.CharField(
        _("SMS Backend"),
        max_length=20,
        choices=SMSBackend.choices,
        default=SMSBackend.TWILIO
    )
    
    account_sid = encrypt(models.CharField(
        _("Account SID/Key"),
        max_length=255,
        blank=True,
        null=True
    ))
    
    auth_token = encrypt(models.CharField(
        _("Auth Token"),
        max_length=255,
        blank=True,
        null=True
    ))
    
    phone_number = models.CharField(
        _("Sender Phone Number"),
        max_length=20,
        help_text=_("In international format (+1234567890)")
    )
    
    api_key = encrypt(models.CharField(
        _("API Key"),
        max_length=255,
        blank=True,
        null=True
    ))
    
    region = models.CharField(
        _("AWS Region"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Only for AWS SNS (e.g., us-east-1)")
    )
    
    timeout = models.PositiveIntegerField(
        _("Connection Timeout"),
        default=10,
        help_text=_("Timeout in seconds for API requests")
    )
    
    is_active = models.BooleanField(
        _("Active Configuration"),
        default=False,
        help_text=_("Only one SMS configuration can be active")
    )


    class Meta:
        verbose_name = _("SMS Configuration")
        verbose_name_plural = _("SMS Configurations")
        constraints = [
            models.UniqueConstraint(
                fields=['is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_sms_config'
            )
        ]

    def clean(self):
        super().clean()
        
        if self.backend == self.SMSBackend.TWILIO and not all([self.account_sid, self.auth_token]):
            raise ValidationError({
                'account_sid': _("Twilio requires Account SID and Auth Token"),
                'auth_token': _("Twilio requires Account SID and Auth Token")
            })
            
        if self.backend == self.SMSBackend.AWS_SNS and not all([self.api_key, self.region]):
            raise ValidationError({
                'api_key': _("AWS SNS requires API Key and Region"),
                'region': _("AWS SNS requires API Key and Region")
            })

    def save(self, *args, **kwargs):
        if self.is_active:
            SMSConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def connection_params(self):
        params = {
            'backend': self.backend,
            'account_sid': self.account_sid,
            'auth_token': self.auth_token,
            'phone_number': self.phone_number,
            'api_key': self.api_key,
            'region': self.region,
            'timeout': self.timeout
        }
        return {k: v for k, v in params.items() if v}

class WhatsAppConfiguration(BaseModel):
    class WhatsAppBackend(models.TextChoices):
        TWILIO = 'TWILIO', _('Twilio')
        META = 'META', _('Meta Business')
        DEBUG = 'DEBUG', _('Debug Console')
    
    name = models.CharField(
        _("Configuration Name"),
        max_length=100,
        unique=True
    )
    
    backend = models.CharField(
        _("WhatsApp Backend"),
        max_length=20,
        choices=WhatsAppBackend.choices,
        default=WhatsAppBackend.TWILIO
    )
    
    account_sid = encrypt(models.CharField(
        _("Account SID"),
        max_length=255,
        blank=True,
        null=True
    ))
    
    auth_token = encrypt(models.CharField(
        _("Auth Token"),
        max_length=255,
        blank=True,
        null=True
    ))
    
    whatsapp_number = models.CharField(
        _("WhatsApp Business Number"),
        max_length=20,
        help_text=_("In international format (+1234567890)")
    )
    
    business_id = models.CharField(
        _("Business ID"),
        max_length=255,
        blank=True,
        null=True
    )
    
    api_version = models.CharField(
        _("API Version"),
        max_length=10,
        default='v1',
        help_text=_("Meta API version (e.g., v15.0)")
    )
    
    timeout = models.PositiveIntegerField(
        _("Connection Timeout"),
        default=15
    )
    
    is_active = models.BooleanField(
        _("Active Configuration"),
        default=False
    )


    class Meta:
        verbose_name = _("WhatsApp Configuration")
        verbose_name_plural = _("WhatsApp Configurations")
        constraints = [
            models.UniqueConstraint(
                fields=['is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_whatsapp_config'
            )
        ]

    def clean(self):
        super().clean()
        
        if self.backend == self.WhatsAppBackend.TWILIO and not all([self.account_sid, self.auth_token]):
            raise ValidationError({
                'account_sid': _("Required for Twilio"),
                'auth_token': _("Required for Twilio")
            })
            
        if self.backend == self.WhatsAppBackend.META and not self.business_id:
            raise ValidationError({
                'business_id': _("Meta Business ID is required")
            })

    def save(self, *args, **kwargs):
        if self.is_active:
            WhatsAppConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def connection_params(self):
        params = {
            'backend': self.backend,
            'account_sid': self.account_sid,
            'auth_token': self.auth_token,
            'whatsapp_number': self.whatsapp_number,
            'business_id': self.business_id,
            'api_version': self.api_version,
            'timeout': self.timeout
        }
        return {k: v for k, v in params.items() if v}

    
class MessageLog(BaseModel):
    """Model to track all messages sent through the system"""
    
    class MessageType(models.TextChoices):
        EMAIL = 'EMAIL', _('Email')
        SMS = 'SMS', _('SMS')
        WHATSAPP = 'WHATSAPP', _('WhatsApp')
    
    class MessageStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SENT = 'SENT', _('Sent')
        DELIVERED = 'DELIVERED', _('Delivered')
        READ = 'READ', _('Read')
        FAILED = 'FAILED', _('Failed')
    
    message_type = models.CharField(
        _("Message Type"),
        max_length=10,
        choices=MessageType.choices
    )
    
    sender = models.CharField(
        _("Sender"),
        max_length=255,
        help_text=_("Email address or phone number of sender")
    )
    
    recipient = models.CharField(
        _("Recipient"),
        max_length=255,
        help_text=_("Email address or phone number of recipient")
    )
    
    cc = models.TextField(
        _("CC Recipients"),
        blank=True,
        null=True,
        help_text=_("Comma-separated list of CC recipients (for emails)")
    )
    
    subject = models.CharField(
        _("Subject"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Email subject or message title")
    )
    
    message = models.TextField(
        _("Message Content"),
        help_text=_("Content of the message")
    )
    
    template_name = models.CharField(
        _("Template Name"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Name of template used, if any")
    )
    
    status = models.CharField(
        _("Status"),
        max_length=10,
        choices=MessageStatus.choices,
        default=MessageStatus.PENDING
    )
    
    sent_at = models.DateTimeField(
        _("Sent Time"),
        blank=True,
        null=True
    )
    
    delivered_at = models.DateTimeField(
        _("Delivery Time"),
        blank=True,
        null=True
    )
    
    read_at = models.DateTimeField(
        _("Read Time"),
        blank=True,
        null=True
    )
    
    provider = models.CharField(
        _("Provider"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Service provider used (Twilio, SendGrid, etc.)")
    )
    
    provider_message_id = models.CharField(
        _("Provider Message ID"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Message ID returned by the provider")
    )
    
    error_message = models.TextField(
        _("Error Message"),
        blank=True,
        null=True,
        help_text=_("Error message if sending failed")
    )
    
    retries = models.PositiveSmallIntegerField(
        _("Retry Count"),
        default=0
    )
    
    metadata = models.JSONField(
        _("Additional Metadata"),
        blank=True,
        null=True,
        help_text=_("Any additional data related to the message")
    )
    
    class Meta:
        verbose_name = _("Message Log")
        verbose_name_plural = _("Message Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message_type', 'status']),
            models.Index(fields=['recipient']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['provider_message_id']),
        ]
    
    def __str__(self):
        return f"{self.message_type} to {self.recipient} ({self.status})"
    
    def update_status(self, status, provider_data=None):
        """Update message status and related fields"""
        self.status = status
        
        # Update timestamps based on status
        now = timezone.now()
        
        if status == self.MessageStatus.SENT and not self.sent_at:
            self.sent_at = now
        elif status == self.MessageStatus.DELIVERED and not self.delivered_at:
            self.delivered_at = now
        elif status == self.MessageStatus.READ and not self.read_at:
            self.read_at = now
        
        # Update provider data if provided
        if provider_data:
            if 'message_id' in provider_data:
                self.provider_message_id = provider_data['message_id']
            if 'error' in provider_data:
                self.error_message = provider_data['error']
            
            # Save any additional metadata
            if not self.metadata:
                self.metadata = {}
            
            self.metadata.update({
                f"update_{now.isoformat()}": provider_data
            })
        
        self.save()
        return self


class ScheduledMessage(BaseModel):
    """Model for scheduling messages to be sent later"""
    
    message_log = models.OneToOneField(
        MessageLog,
        on_delete=models.CASCADE,
        related_name='schedule',
        help_text=_("Associated message log entry")
    )
    
    scheduled_time = models.DateTimeField(
        _("Scheduled Time"),
        help_text=_("When the message should be sent")
    )
    
    recurring = models.BooleanField(
        _("Recurring Message"),
        default=False
    )
    
    recurrence_pattern = models.JSONField(
        _("Recurrence Pattern"),
        blank=True,
        null=True,
        help_text=_("JSON defining recurrence rules")
    )
    
    processed = models.BooleanField(
        _("Processed"),
        default=False,
        help_text=_("Whether this scheduled message has been processed")
    )
    
    canceled = models.BooleanField(
        _("Canceled"),
        default=False
    )
    
    last_run = models.DateTimeField(
        _("Last Run Time"),
        blank=True,
        null=True
    )
    
    next_run = models.DateTimeField(
        _("Next Run Time"),
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _("Scheduled Message")
        verbose_name_plural = _("Scheduled Messages")
        ordering = ['scheduled_time']
        indexes = [
            models.Index(fields=['scheduled_time']),
            models.Index(fields=['processed']),
            models.Index(fields=['recurring']),
            models.Index(fields=['next_run']),
        ]
    
    def __str__(self):
        status = "Scheduled"
        if self.processed:
            status = "Sent"
        if self.canceled:
            status = "Canceled"
        
        return f"{self.message_log.message_type} to {self.message_log.recipient} ({status} for {self.scheduled_time})"
    
    def cancel(self):
        """Cancel this scheduled message"""
        self.canceled = True
        self.save()
        return self
    
    def calculate_next_run(self):
        """Calculate next run time based on recurrence pattern"""
        if not self.recurring or not self.recurrence_pattern:
            return None
        
        from dateutil.relativedelta import relativedelta
        
        # Get the last run time or scheduled time if never run
        base_time = self.last_run or self.scheduled_time
        pattern = self.recurrence_pattern
        
        # Calculate next run based on pattern
        if pattern.get('frequency') == 'daily':
            next_time = base_time + relativedelta(days=pattern.get('interval', 1))
        elif pattern.get('frequency') == 'weekly':
            next_time = base_time + relativedelta(weeks=pattern.get('interval', 1))
        elif pattern.get('frequency') == 'monthly':
            next_time = base_time + relativedelta(months=pattern.get('interval', 1))
        elif pattern.get('frequency') == 'yearly':
            next_time = base_time + relativedelta(years=pattern.get('interval', 1))
        else:
            return None
        
        # Update next_run field
        self.next_run = next_time
        self.save(update_fields=['next_run'])
        
        return next_time


class MessageTemplate(BaseModel):
    """Model for storing message templates"""
    
    class TemplateType(models.TextChoices):
        EMAIL = 'EMAIL', _('Email')
        SMS = 'SMS', _('SMS')
        WHATSAPP = 'WHATSAPP', _('WhatsApp')
    
    name = models.CharField(
        _("Template Name"),
        max_length=100,
        unique=True
    )
    
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True
    )
    
    template_type = models.CharField(
        _("Template Type"),
        max_length=10,
        choices=TemplateType.choices
    )
    
    subject = models.CharField(
        _("Subject"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Subject line for email templates")
    )
    
    content = models.TextField(
        _("Template Content"),
        help_text=_("Template content with variable placeholders")
    )
    
    html_content = models.TextField(
        _("HTML Content"),
        blank=True,
        null=True,
        help_text=_("HTML version for email templates")
    )
    
    default_context = models.JSONField(
        _("Default Context"),
        blank=True,
        null=True,
        help_text=_("Default values for template variables")
    )
    
    is_active = models.BooleanField(
        _("Active"),
        default=True
    )
    
    class Meta:
        verbose_name = _("Message Template")
        verbose_name_plural = _("Message Templates")
        ordering = ['name']
        indexes = [
            models.Index(fields=['template_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def render(self, context=None):
        """
        Render the template with given context
        
        Args:
            context (dict): Context variables for template
            
        Returns:
            dict: With keys 'subject', 'content', 'html_content'
        """
        from django.template import Template, Context
        
        # Merge default context with provided context
        merged_context = self.default_context or {}
        if context:
            merged_context.update(context)
        
        template_context = Context(merged_context)
        
        # Render content
        content_template = Template(self.content)
        rendered_content = content_template.render(template_context)
        
        # Render subject if present
        rendered_subject = None
        if self.subject:
            subject_template = Template(self.subject)
            rendered_subject = subject_template.render(template_context)
        
        # Render HTML content if present
        rendered_html = None
        if self.html_content:
            html_template = Template(self.html_content)
            rendered_html = html_template.render(template_context)
        
        return {
            'subject': rendered_subject,
            'content': rendered_content,
            'html_content': rendered_html
        }

