# apps/notifications/backend/test_email_backend.py

import logging
import traceback
from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend
from django.core.mail.backends.console import EmailBackend as DjangoConsoleBackend
from django.utils import timezone
from django.conf import settings

from apps.notifications.models.emailmodel import EmailConfiguration, MessageLog

logger = logging.getLogger(__name__)

class TestEmailBackend:
    """
    Backend para pruebas de correo electrónico
    
    Esta implementación permite probar el envío de correos usando directamente
    los backends estándar de Django, pero registrando el resultado en la base de datos
    y proporcionando mejor información de depuración.
    """
    
    def __init__(self, config=None, use_console=False, fail_silently=False, **kwargs):
        self.config = config
        self.use_console = use_console
        self.fail_silently = fail_silently
        self.connection = None
        self.extra_kwargs = kwargs
        self.log_entry = None
    
    def open(self):
        """Abre una conexión al servidor de correo"""
        if self.connection:
            return False
        
        try:
            if self.use_console:
                logger.info("Usando backend de consola para pruebas")
                self.connection = DjangoConsoleBackend(fail_silently=self.fail_silently)
                return self.connection.open()
            
            if not self.config:
                logger.warning("No se proporcionó configuración para el backend de correo")
                if hasattr(settings, 'EMAIL_HOST'):
                    # Usar configuración de settings.py
                    logger.info("Usando configuración de settings.py")
                    self.connection = DjangoSMTPBackend(
                        host=settings.EMAIL_HOST,
                        port=settings.EMAIL_PORT,
                        username=settings.EMAIL_HOST_USER,
                        password=settings.EMAIL_HOST_PASSWORD,
                        use_tls=getattr(settings, 'EMAIL_USE_TLS', False),
                        use_ssl=getattr(settings, 'EMAIL_USE_SSL', False),
                        timeout=getattr(settings, 'EMAIL_TIMEOUT', 30),
                        fail_silently=self.fail_silently
                    )
                    return self.connection.open()
                else:
                    # Fallback a consola
                    logger.warning("No hay configuración SMTP disponible, usando consola")
                    self.connection = DjangoConsoleBackend(fail_silently=self.fail_silently)
                    return self.connection.open()
            
            # Usar la configuración proporcionada
            logger.info(f"Configurando conexión SMTP con: {self.config.host}:{self.config.port}")
            self.connection = DjangoSMTPBackend(
                host=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                use_tls=self.config.security_protocol in ['TLS', 'STARTTLS'],
                use_ssl=self.config.security_protocol == 'SSL',
                timeout=self.config.timeout,
                fail_silently=self.fail_silently or self.config.fail_silently,
                **self.extra_kwargs
            )
            return self.connection.open()
            
        except Exception as e:
            logger.error(f"Error al abrir conexión SMTP: {e}")
            if not self.fail_silently:
                raise
            return False
    
    def close(self):
        """Cierra la conexión al servidor de correo"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def create_log_entry(self, email_message):
        """Crea una entrada de log para el mensaje"""
        try:
            self.log_entry = MessageLog.objects.create(
                message_type="EMAIL",
                sender=email_message.from_email,
                recipient=", ".join(email_message.to),
                cc=", ".join(email_message.cc) if email_message.cc else None,
                subject=email_message.subject,
                message=email_message.body,
                status="PENDING",
                provider=f"TestEmailBackend ({'Console' if self.use_console else 'SMTP'})",
                metadata={
                    "headers": dict(email_message.extra_headers),
                    "attachments": len(email_message.attachments),
                    "test_mode": True
                }
            )
            logger.debug(f"Creada entrada de log: {self.log_entry.pk}")
        except Exception as e:
            logger.error(f"Error al crear entrada de log: {e}")
            self.log_entry = None
    
    def update_log_status(self, status, message_id=None, error=None):
        """Actualiza el estado de la entrada de log"""
        if not self.log_entry:
            return
        
        try:
            self.log_entry.status = status
            
            # Actualizar campos adicionales según el estado
            if status == "SENT":
                self.log_entry.sent_at = timezone.now()
                if message_id:
                    self.log_entry.provider_message_id = message_id
            elif status == "FAILED":
                self.log_entry.error_message = error
            
            # Guardar metadatos adicionales
            if not self.log_entry.metadata:
                self.log_entry.metadata = {}
            
            if error:
                self.log_entry.metadata["error_details"] = error
            
            self.log_entry.save()
            logger.debug(f"Actualizado log {self.log_entry.pk} a estado: {status}")
        except Exception as e:
            logger.error(f"Error al actualizar log: {e}")
    
    def send_messages(self, email_messages):
        """Envía una lista de mensajes de correo electrónico"""
        if not email_messages:
            return 0
        
        # Asegurar que la conexión esté abierta
        if not self.connection:
            if not self.open():
                logger.error("No se pudo abrir la conexión para enviar mensajes")
                if not self.fail_silently:
                    raise Exception("No se pudo establecer conexión con el servidor de correo")
                return 0
        
        # Contador de mensajes enviados
        num_sent = 0
        
        # Procesar cada mensaje
        for message in email_messages:
            try:
                # Crear entrada de log para este mensaje
                self.create_log_entry(message)
                
                # Intentar enviar el mensaje
                logger.info(f"Enviando mensaje a {', '.join(message.to)} desde {message.from_email}")
                sent = self.connection.send_messages([message])
                
                if sent:
                    num_sent += 1
                    logger.info(f"Mensaje enviado exitosamente a {', '.join(message.to)}")
                    self.update_log_status("SENT")
                else:
                    logger.warning(f"El mensaje no se envió a {', '.join(message.to)}")
                    self.update_log_status("FAILED", error="No se recibió confirmación de envío")
                
            except Exception as e:
                logger.error(f"Error al enviar mensaje: {e}")
                error_traceback = traceback.format_exc()
                logger.debug(f"Detalles del error: {error_traceback}")
                
                # Actualizar log con el error
                self.update_log_status("FAILED", error=f"{str(e)}\n{error_traceback}")
                
                if not self.fail_silently:
                    raise
        
        return num_sent
    
    def __enter__(self):
        """Soporte para uso con 'with'"""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra la conexión al salir del bloque 'with'"""
        self.close()
        return False  # No suprimir excepciones


# Función de conveniencia para pruebas rápidas
def send_test_email(subject, message, from_email, recipient_list,
                   config=None, use_console=False, fail_silently=False,
                   html_message=None, connection=None, **kwargs):
    """
    Función de conveniencia para enviar un correo de prueba y registrar el resultado.
    
    Args:
        subject: Asunto del correo
        message: Contenido del correo en texto plano
        from_email: Dirección del remitente
        recipient_list: Lista de destinatarios
        config: Instancia de EmailConfiguration (opcional)
        use_console: Si es True, usa el backend de consola
        fail_silently: Si es True, no levanta excepciones
        html_message: Contenido del correo en HTML (opcional)
        connection: Conexión existente (opcional)
        **kwargs: Parámetros adicionales
        
    Returns:
        Tupla (éxito, log_entry, error_message)
    """
    try:
        # Usar configuración activa si no se proporciona una
        if not config and not use_console and not connection:
            config = EmailConfiguration.get_active_configuration()
            if not config:
                logger.warning("No hay configuración activa, usando consola")
                use_console = True
        
        # Crear una conexión si no se proporcionó una
        if not connection:
            connection = TestEmailBackend(
                config=config,
                use_console=use_console,
                fail_silently=fail_silently
            )
        
        # Enviar el correo utilizando la función estándar de Django
        from django.core.mail import send_mail
        result = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=fail_silently,
            auth_user=None,
            auth_password=None,
            connection=connection,
            html_message=html_message
        )
        
        # Obtener la entrada de log creada
        log_entry = connection.log_entry
        
        # Devolver resultado
        return (result > 0, log_entry, None)
        
    except Exception as e:
        logger.exception(f"Error al enviar correo de prueba: {e}")
        error_message = f"{str(e)}\n{traceback.format_exc()}"
        return (False, None, error_message)