# notifications/backends.py

import logging
from typing import Dict, Any
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings # For Django's default EMAIL_* settings if needed

# Import necessary libraries (install them first!)
try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
except ImportError:
    TwilioClient = None
    TwilioRestException = None

try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content
except ImportError:
    sendgrid = None
    Mail = None # Avoid runtime errors if not installed

from apps.notifications.models.emailmodel import MessageLog, EmailConfiguration, SMSConfiguration, WhatsAppConfiguration

logger = logging.getLogger(__name__)

# --- Email Backends ---

def send_email_via_backend(config: EmailConfiguration, log_entry: MessageLog) -> Dict[str, Any]:
    """Dispatches email sending based on the active configuration's backend."""
    backend_map = {
        EmailConfiguration.EmailBackend.SMTP: _send_smtp_email,
        EmailConfiguration.EmailBackend.SENDGRID: _send_sendgrid_email,
        EmailConfiguration.EmailBackend.CONSOLE: _send_console_email,
        # Add other backends (SES, FILE) here
    }
    send_func = backend_map.get(config.backend)

    if not send_func:
        raise NotImplementedError(f"Email backend '{config.backend}' is not implemented.")

    # Retrieve HTML content if stored in metadata
    html_content = log_entry.metadata.get('html_content') if log_entry.metadata else None

    return send_func(config, log_entry, html_content)

def _send_smtp_email(config: EmailConfiguration, log_entry: MessageLog, html_content: str = None) -> Dict[str, Any]:
    """Sends email using Django's SMTP backend configured dynamically."""
    from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend

    # Create a backend instance with dynamic settings from config
    backend = SMTPEmailBackend(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password, # Assumes decrypted password if using django-cryptography
        use_tls=config.security_protocol == EmailConfiguration.SecurityProtocol.TLS,
        use_ssl=config.security_protocol == EmailConfiguration.SecurityProtocol.SSL,
        timeout=config.timeout,
        fail_silently=False # We handle exceptions in the task
    )

    subject = log_entry.subject
    body = log_entry.message
    from_email = log_entry.sender # Use sender from log (which might be default from config)
    recipient_list = [log_entry.recipient]
    if log_entry.cc:
        recipient_list.extend([email.strip() for email in log_entry.cc.split(',')])

    try:
        if html_content:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=from_email,
                to=[log_entry.recipient], # `to` expects a list/tuple
                cc=[email.strip() for email in log_entry.cc.split(',')] if log_entry.cc else None,
                connection=backend, # Use the configured backend
            )
            msg.attach_alternative(html_content, "text/html")
            sent_count = msg.send(fail_silently=False)
        else:
            sent_count = backend.send_messages([
                 EmailMultiAlternatives(subject, body, from_email, recipient_list)
            ])
            # Or use simpler send_mail with the backend connection
            # sent_count = send_mail(
            #     subject, body, from_email, recipient_list,
            #     fail_silently=False, connection=backend
            # )

        if sent_count > 0:
            return {'status': 'sent', 'provider_message_id': None} # SMTP usually doesn't give IDs easily
        else:
            raise Exception("SMTP backend reported 0 messages sent.")

    except Exception as e:
        logger.error(f"SMTP Send Error: {e}", exc_info=True)
        raise # Re-raise for the task to handle

def _send_sendgrid_email(config: EmailConfiguration, log_entry: MessageLog, html_content: str = None) -> Dict[str, Any]:
    """Sends email using the SendGrid API."""
    if not sendgrid or not Mail:
        raise ImportError("SendGrid library not installed. Run 'pip install sendgrid'")
    if not config.api_key:
        raise ValueError("SendGrid API Key is missing in the configuration.")

    sg = sendgrid.SendGridAPIClient(api_key=config.api_key)
    from_email = Email(log_entry.sender) # Assumes sender is valid email format
    to_email = To(log_entry.recipient)

    # Prioritize HTML content if available
    if html_content:
        content = Content("text/html", html_content)
        # Optionally include plain text version as well
        # mail.add_content(Content("text/plain", log_entry.message))
    else:
        content = Content("text/plain", log_entry.message)

    mail = Mail(from_email, to_email, log_entry.subject, content)

    # Add CC if present
    if log_entry.cc:
        for cc_email in [email.strip() for email in log_entry.cc.split(',')]:
            mail.add_cc(cc_email)

    try:
        response = sg.client.mail.send.post(request_body=mail.get())
        logger.debug(f"SendGrid Response Status: {response.status_code}")
        logger.debug(f"SendGrid Response Body: {response.body}")
        logger.debug(f"SendGrid Response Headers: {response.headers}")

        if 200 <= response.status_code < 300:
             # Extract message ID if possible (check SendGrid docs for header name)
             message_id = response.headers.get('X-Message-Id')
             return {'status': 'sent', 'provider_message_id': message_id}
        else:
            raise Exception(f"SendGrid API Error ({response.status_code}): {response.body}")

    except Exception as e:
        logger.error(f"SendGrid Send Error: {e}", exc_info=True)
        raise

def _send_console_email(config: EmailConfiguration, log_entry: MessageLog, html_content: str = None) -> Dict[str, Any]:
    """'Sends' email to the console for debugging."""
    print("-" * 20)
    print(f"--- CONSOLE EMAIL ({config.name}) ---")
    print(f"To: {log_entry.recipient}")
    if log_entry.cc: print(f"CC: {log_entry.cc}")
    print(f"From: {log_entry.sender}")
    print(f"Subject: {log_entry.subject}")
    print("--- Body (Text) ---")
    print(log_entry.message)
    if html_content:
        print("--- Body (HTML) ---")
        print(html_content)
    print("-" * 20)
    return {'status': 'sent', 'provider_message_id': f'console-{log_entry.pk}'}


# --- SMS Backends ---

def send_sms_via_backend(config: SMSConfiguration, log_entry: MessageLog) -> Dict[str, Any]:
    """Dispatches SMS sending based on the active configuration's backend."""
    backend_map = {
        SMSConfiguration.SMSBackend.TWILIO: _send_twilio_sms,
        SMSConfiguration.SMSBackend.DEBUG: _send_debug_sms,
        # Add other backends (AWS SNS, Plivo, Nexmo) here
    }
    send_func = backend_map.get(config.backend)

    if not send_func:
        raise NotImplementedError(f"SMS backend '{config.backend}' is not implemented.")

    return send_func(config, log_entry)

def _send_twilio_sms(config: SMSConfiguration, log_entry: MessageLog) -> Dict[str, Any]:
    """Sends SMS using the Twilio API."""
    if not TwilioClient:
        raise ImportError("Twilio library not installed. Run 'pip install twilio'")
    if not all([config.account_sid, config.auth_token, config.phone_number]):
         raise ValueError("Twilio configuration (SID, Token, From Number) is incomplete.")

    client = TwilioClient(config.account_sid, config.auth_token) # Assumes decrypted credentials

    try:
        message = client.messages.create(
            body=log_entry.message,
            from_=config.phone_number, # Twilio sender number
            to=log_entry.recipient      # Recipient number
            # Add status_callback URL here if you want delivery updates
        )
        logger.info(f"Twilio SMS sent. SID: {message.sid}, Status: {message.status}")
        # Twilio message creation is usually synchronous success/fail
        # Status might be 'queued', 'sending', 'sent', 'failed', etc.
        # We consider 'queued' or 'sent' as success for this step.
        if message.status in ['queued', 'sending', 'sent']:
             return {'status': 'sent', 'provider_message_id': message.sid}
        else:
             # Capture error details if available
             error_code = getattr(message, 'error_code', None)
             error_message = getattr(message, 'error_message', f"Twilio status: {message.status}")
             raise TwilioRestException(status=message.status, uri=message.uri, msg=error_message, code=error_code)

    except TwilioRestException as e:
        logger.error(f"Twilio SMS Error: {e}", exc_info=True)
        raise Exception(f"Twilio API Error: {e}") # Wrap for consistent handling in task
    except Exception as e:
        logger.error(f"Twilio SMS Send Error: {e}", exc_info=True)
        raise

def _send_debug_sms(config: SMSConfiguration, log_entry: MessageLog) -> Dict[str, Any]:
    """'Sends' SMS to the console for debugging."""
    print("-" * 20)
    print(f"--- DEBUG SMS ({config.name}) ---")
    print(f"To: {log_entry.recipient}")
    print(f"From: {config.phone_number}") # Use configured sender
    print("--- Body ---")
    print(log_entry.message)
    print("-" * 20)
    return {'status': 'sent', 'provider_message_id': f'debug-sms-{log_entry.pk}'}


# --- WhatsApp Backends ---

def send_whatsapp_via_backend(config: WhatsAppConfiguration, log_entry: MessageLog) -> Dict[str, Any]:
    """Dispatches WhatsApp sending based on the active configuration's backend."""
    backend_map = {
        WhatsAppConfiguration.WhatsAppBackend.TWILIO: _send_twilio_whatsapp,
        WhatsAppConfiguration.WhatsAppBackend.DEBUG: _send_debug_whatsapp,
        # Add Meta backend here
    }
    send_func = backend_map.get(config.backend)

    if not send_func:
        raise NotImplementedError(f"WhatsApp backend '{config.backend}' is not implemented.")

    return send_func(config, log_entry)

def _send_twilio_whatsapp(config: WhatsAppConfiguration, log_entry: MessageLog) -> Dict[str, Any]:
    """Sends WhatsApp message using the Twilio API."""
    if not TwilioClient:
        raise ImportError("Twilio library not installed. Run 'pip install twilio'")
    if not all([config.account_sid, config.auth_token, config.whatsapp_number]):
         raise ValueError("Twilio WhatsApp configuration (SID, Token, From Number) is incomplete.")

    client = TwilioClient(config.account_sid, config.auth_token)

    # Ensure numbers are in Twilio's expected format (e.g., whatsapp:+1234567890)
    from_whatsapp = f"whatsapp:{config.whatsapp_number}"
    to_whatsapp = f"whatsapp:{log_entry.recipient}"

    try:
        # Note: Twilio WhatsApp often requires pre-approved templates for business-initiated messages
        # outside the 24-hour customer care window. Sending freeform text might fail.
        # This example sends freeform text. Adapt if using templates.
        message = client.messages.create(
            body=log_entry.message,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        logger.info(f"Twilio WhatsApp sent. SID: {message.sid}, Status: {message.status}")

        if message.status in ['queued', 'sending', 'sent']:
             return {'status': 'sent', 'provider_message_id': message.sid}
        else:
             error_code = getattr(message, 'error_code', None)
             error_message = getattr(message, 'error_message', f"Twilio status: {message.status}")
             raise TwilioRestException(status=message.status, uri=message.uri, msg=error_message, code=error_code)

    except TwilioRestException as e:
        logger.error(f"Twilio WhatsApp Error: {e}", exc_info=True)
        raise Exception(f"Twilio API Error: {e}")
    except Exception as e:
        logger.error(f"Twilio WhatsApp Send Error: {e}", exc_info=True)
        raise

def _send_debug_whatsapp(config: WhatsAppConfiguration, log_entry: MessageLog) -> Dict[str, Any]:
    """'Sends' WhatsApp message to the console for debugging."""
    print("-" * 20)
    print(f"--- DEBUG WHATSAPP ({config.name}) ---")
    print(f"To: whatsapp:{log_entry.recipient}")
    print(f"From: whatsapp:{config.whatsapp_number}") # Use configured sender
    print("--- Body ---")
    print(log_entry.message)
    print("-" * 20)
    return {'status': 'sent', 'provider_message_id': f'debug-whatsapp-{log_entry.pk}'}