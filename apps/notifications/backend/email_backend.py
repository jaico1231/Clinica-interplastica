# apps/notifications/backend/email_backend.py

import logging
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
from django.core.mail.backends.filebased import EmailBackend as FilebasedEmailBackend
from django.core.exceptions import ImproperlyConfigured

# --- Import third-party backends safely ---
try:
    # Assumes you are using django-sendgrid-v5 or a similar package
    from sendgrid_backend import SendgridBackend
except ImportError:
    SendgridBackend = None

try:
    # Assumes you are using django-ses
    from django_ses import SESBackend
except ImportError:
    SESBackend = None
# -----------------------------------------

from apps.notifications.models.emailmodel import EmailConfiguration # Ajusta la ruta si es necesario

logger = logging.getLogger(__name__)

class DatabaseEmailBackend(BaseEmailBackend):
    """
    A Django Email Backend that uses EmailConfiguration from the database.
    Dynamically selects and configures the appropriate backend (SMTP, SendGrid, SES, etc.).
    """
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self._connection = None
        self.config = None # Stores the active EmailConfiguration instance

    def open(self):
        """
        Fetches the active EmailConfiguration from the DB and establishes
        a connection using the corresponding backend.
        Returns True if a connection was successfully opened, False otherwise.
        """
        if self._connection:
            return True # Connection already active

        self.config = EmailConfiguration.get_active_configuration()

        if not self.config:
            logger.warning("No active EmailConfiguration found in database. Falling back to console backend.")
            # Define a default fallback configuration (e.g., console)
            # Or raise an error if no config is unacceptable:
            # raise ImproperlyConfigured("No active EmailConfiguration found in the database.")
            self.config = EmailConfiguration(
                name="Fallback Console",
                backend=EmailConfiguration.EmailBackend.CONSOLE,
                is_active=False # Mark as inactive as it's just a fallback
            )

        backend_choice = self.config.backend
        config_name = self.config.name or "Fallback"
        logger.debug(f"Attempting to open email connection using backend: {backend_choice} (Config: '{config_name}')")

        try:
            # --- SMTP Backend ---
            if backend_choice == EmailConfiguration.EmailBackend.SMTP:
                params = self.config.connection_params # Use the property from the model
                # Ensure boolean flags are correct based on security protocol
                params['use_tls'] = self.config.security_protocol in [EmailConfiguration.SecurityProtocol.TLS, EmailConfiguration.SecurityProtocol.STARTTLS]
                params['use_ssl'] = self.config.security_protocol == EmailConfiguration.SecurityProtocol.SSL
                # Filter only relevant SMTP params, removing None values
                smtp_params = {
                    k: v for k, v in params.items()
                    if v is not None and k in ['host', 'port', 'username', 'password', 'use_tls', 'use_ssl', 'timeout']
                }
                if not smtp_params.get('host'):
                     raise ImproperlyConfigured(f"SMTP backend requires 'host' in EmailConfiguration '{config_name}'.")

                self._connection = SMTPEmailBackend(fail_silently=self.fail_silently, **smtp_params)
                logger.info(f"SMTP connection configured for host: {smtp_params.get('host')}:{smtp_params.get('port')}")

            # --- SendGrid Backend ---
            elif backend_choice == EmailConfiguration.EmailBackend.SENDGRID:
                if SendgridBackend is None:
                    raise ImproperlyConfigured("SendGrid backend selected, but 'sendgrid_backend' (from django-sendgrid-v5) is not installed or importable.")
                if not self.config.api_key:
                    raise ImproperlyConfigured(f"SendGrid backend requires 'api_key' in EmailConfiguration '{config_name}'.")

                # django-sendgrid-v5 primarily uses settings.SENDGRID_API_KEY.
                # We instantiate it here, and it should pick up the key from settings.
                # If you *must* force the key from the DB, you might need to subclass SendgridBackend
                # or check if it accepts api_key in its __init__ (consult its documentation).
                # For now, we rely on the standard mechanism but log a warning if DB key exists.
                settings_api_key = getattr(settings, 'SENDGRID_API_KEY', None)
                if not settings_api_key and self.config.api_key:
                     logger.warning(f"SendGrid config '{config_name}' has an API key, but SENDGRID_API_KEY is not set in Django settings. The backend might fail if it relies solely on settings.")
                     # If the backend allows passing the key directly (check docs):
                     # self._connection = SendgridBackend(fail_silently=self.fail_silently, api_key=self.config.api_key)
                elif settings_api_key != self.config.api_key:
                     logger.warning(f"API key in SendGrid config '{config_name}' differs from settings.SENDGRID_API_KEY. The backend will likely use the key from settings.")

                # Instantiate using the library's default mechanism (likely reads from settings)
                self._connection = SendgridBackend(fail_silently=self.fail_silently)
                logger.info("SendGrid connection configured (relies on SENDGRID_API_KEY in settings).")


            # --- Amazon SES Backend ---
            elif backend_choice == EmailConfiguration.EmailBackend.SES:
                if SESBackend is None:
                    raise ImproperlyConfigured("SES backend selected, but 'django_ses' is not installed or importable.")

                # django-ses automatically finds credentials via:
                # 1. AWS Credentials in settings (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
                # 2. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
                # 3. IAM role attached to the EC2 instance or ECS task, etc.
                # Our DB model doesn't (and generally shouldn't) store these credentials.
                self._connection = SESBackend(fail_silently=self.fail_silently)
                # You might want to add checks here if credentials are required but not found,
                # although django-ses might raise its own errors later.
                logger.info("Amazon SES connection configured (relies on AWS credentials in settings, environment, or IAM role).")


            # --- Console Backend ---
            elif backend_choice == EmailConfiguration.EmailBackend.CONSOLE:
                self._connection = ConsoleEmailBackend(fail_silently=self.fail_silently)
                logger.info("Console email backend configured.")

            # --- File Backend ---
            elif backend_choice == EmailConfiguration.EmailBackend.FILE:
                file_path = getattr(settings, 'EMAIL_FILE_PATH', None)
                if not file_path:
                    raise ImproperlyConfigured("File backend selected, but EMAIL_FILE_PATH is not defined in Django settings.")
                self._connection = FilebasedEmailBackend(file_path=file_path, fail_silently=self.fail_silently)
                logger.info(f"File email backend configured (path: {file_path}).")

            # --- Unsupported Backend ---
            else:
                raise NotImplementedError(f"The email backend '{backend_choice}' specified in configuration '{config_name}' is not supported by DatabaseEmailBackend.")

            # --- Open the actual backend connection ---
            # Some backends might not require an explicit open(), but call it if available.
            if hasattr(self._connection, 'open') and callable(getattr(self._connection, 'open')):
                self._connection.open()

            logger.debug(f"Successfully opened connection for backend: {backend_choice}")
            return True # Connection successful

        except ImproperlyConfigured as e:
            logger.error(f"Configuration error for email backend {backend_choice}: {e}", exc_info=True)
            if not self.fail_silently:
                raise # Re-raise configuration errors unless fail_silently is True
            self._connection = None
            return False
        except Exception as e:
            logger.error(f"Failed to open email connection using backend {backend_choice} (Config: '{config_name}'): {e}", exc_info=True)
            if not self.fail_silently:
                raise # Re-raise unexpected errors
            self._connection = None # Ensure connection is reset on failure
            return False

    def close(self):
        """Closes the connection to the underlying email backend."""
        if self._connection is None:
            return
        try:
            if hasattr(self._connection, 'close') and callable(getattr(self._connection, 'close')):
                self._connection.close()
            logger.debug(f"Closed connection for backend: {self.config.backend if self.config else 'N/A'}")
        except Exception as e:
            logger.error(f"Error closing email connection: {e}", exc_info=True)
            if not self.fail_silently:
                raise
        finally:
            self._connection = None
            self.config = None # Clear the config reference when closed

    def send_messages(self, email_messages):
        """
        Sends one or more EmailMessage objects using the active backend.
        Returns the number of email messages sent.
        """
        if not email_messages:
            return 0

        # Ensure connection is open, attempting to open if necessary
        if self._connection is None:
            if not self.open():
                logger.error("Cannot send messages, failed to open email connection.")
                return 0 # Connection failed, cannot send

        # --- Pre-processing messages based on active config ---
        if self.config:
            default_from = self.config.from_email
            use_headers = self.config.use_custom_headers
            custom_headers = self.config.custom_headers if use_headers else None

            for message in email_messages:
                # Set default 'from_email' if not provided in the message
                if not message.from_email and default_from:
                    message.from_email = default_from

                # Add custom headers if configured and enabled
                if use_headers and custom_headers:
                    if not isinstance(message.extra_headers, dict):
                        message.extra_headers = {}
                    # Add/override headers from config (config headers take precedence)
                    message.extra_headers.update(custom_headers)
        # -----------------------------------------------------

        try:
            # Delegate sending to the actual backend's connection
            num_sent = self._connection.send_messages(email_messages)
            logger.info(f"Sent {num_sent} message(s) using backend: {self.config.backend}")
            return num_sent
        except Exception as e:
            logger.error(f"Error sending email using backend {self.config.backend}: {e}", exc_info=True)
            if not self.fail_silently:
                raise
            return 0 # Sending failed
        # finally:
            # Decide whether to close the connection after each batch.
            # Keeping it open can be more efficient for sending multiple batches quickly.
            # Closing ensures resources are released promptly.
            # self.close()