# notifications/services.py

import logging
from typing import Optional, Dict, List, Any
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.notifications.models.emailmodel import (
    MessageLog, MessageTemplate, ScheduledMessage,
    EmailConfiguration, SMSConfiguration, WhatsAppConfiguration)
from apps.notifications.tasks.notifications_task import process_notification_task


# from .tasks import process_notification_task # Importaremos la tarea de Celery

logger = logging.getLogger(__name__)

def send_notification(
    message_type: MessageLog.MessageType,
    recipient: str,
    subject: Optional[str] = None,
    message_body: Optional[str] = None,
    html_message_body: Optional[str] = None,
    template_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    sender: Optional[str] = None,
    cc: Optional[List[str]] = None,
    scheduled_time: Optional[timezone.datetime] = None,
    metadata: Optional[Dict[str, Any]] = None,
    fail_silently: bool = False,
) -> Optional[MessageLog]:
    """
    Main service function to send or schedule a notification.

    Args:
        message_type: Type of message (EMAIL, SMS, WHATSAPP).
        recipient: Primary recipient address/number.
        subject: Subject (mainly for EMAIL).
        message_body: Plain text content.
        html_message_body: HTML content (for EMAIL).
        template_name: Name of the MessageTemplate to use.
        context: Dictionary context for rendering the template.
        sender: Sender address/number (optional, uses default from config).
        cc: List of CC recipients (for EMAIL).
        scheduled_time: If set, schedule the message for later sending.
        metadata: Additional data to store with the log.
        fail_silently: If True, suppress exceptions during log creation/scheduling.

    Returns:
        The created MessageLog instance or None if failed silently.
    """
    log_entry = None
    try:
        # 1. Resolve Sender (if not provided)
        if not sender:
            sender = _get_default_sender(message_type)
            if not sender:
                 raise ValueError(f"No active configuration or default sender found for {message_type}")

        # 2. Render Template (if provided)
        rendered_content = {}
        if template_name:
            try:
                template = MessageTemplate.objects.get(name=template_name, template_type=message_type, is_active=True)
                rendered_content = template.render(context or {})
                subject = subject or rendered_content.get('subject')
                message_body = message_body or rendered_content.get('content')
                html_message_body = html_message_body or rendered_content.get('html_content')
            except MessageTemplate.DoesNotExist:
                raise ValueError(f"Active template '{template_name}' of type '{message_type}' not found.")
            except Exception as e:
                raise ValueError(f"Error rendering template '{template_name}': {e}")

        # Basic validation
        if not recipient:
            raise ValueError("Recipient cannot be empty.")
        if message_type == MessageLog.MessageType.EMAIL and not subject:
             raise ValueError("Subject is required for email messages.")
        if not message_body and not html_message_body:
             raise ValueError("Message body (text or HTML) is required.")

        # 3. Create MessageLog entry
        log_entry = MessageLog.objects.create(
            message_type=message_type,
            sender=sender,
            recipient=recipient,
            cc=", ".join(cc) if cc else None, # Store CC as comma-separated string
            subject=subject,
            message=message_body or '', # Ensure message is not None
            # Store HTML separately if needed, or combine/prioritize in backend
            # For simplicity here, we store plain text. Backends can handle HTML.
            template_name=template_name,
            status=MessageLog.MessageStatus.PENDING,
            metadata=metadata,
            # Add created_by if using CompleteModel and request context is available
        )
        # Store HTML content in metadata if desired, or add a dedicated field to MessageLog
        if html_message_body:
             log_entry.metadata = log_entry.metadata or {}
             log_entry.metadata['html_content'] = html_message_body
             log_entry.save(update_fields=['metadata'])


        # 4. Schedule or Send Asynchronously
        if scheduled_time:
            if scheduled_time <= timezone.now():
                raise ValueError("Scheduled time must be in the future.")
            ScheduledMessage.objects.create(
                message_log=log_entry,
                scheduled_time=scheduled_time
                # Add recurrence logic here if needed based on input params
            )
            logger.info(f"Scheduled {message_type} to {recipient} for {scheduled_time}. Log ID: {log_entry.pk}")
        else:
            # Enqueue the task for immediate processing
            process_notification_task.delay(log_entry.pk)
            logger.info(f"Enqueued {message_type} to {recipient} for sending. Log ID: {log_entry.pk}")

        return log_entry

    except Exception as e:
        logger.error(f"Failed to create/schedule notification ({message_type} to {recipient}): {e}", exc_info=True)
        # Optionally update log status to FAILED here if log_entry was created
        if log_entry and log_entry.status == MessageLog.MessageStatus.PENDING:
             log_entry.status = MessageLog.MessageStatus.FAILED
             log_entry.error_message = f"Failed during preparation/scheduling: {e}"
             log_entry.save(update_fields=['status', 'error_message'])

        if not fail_silently:
            raise # Re-raise the exception if not failing silently
        return None


def _get_default_sender(message_type: MessageLog.MessageType) -> Optional[str]:
    """Helper to get the default sender from the active configuration."""
    config = None
    sender_field = None
    if message_type == MessageLog.MessageType.EMAIL:
        config = EmailConfiguration.get_active_configuration()
        sender_field = 'from_email'
    elif message_type == MessageLog.MessageType.SMS:
        config = SMSConfiguration.objects.filter(is_active=True).first()
        sender_field = 'phone_number'
    elif message_type == MessageLog.MessageType.WHATSAPP:
        config = WhatsAppConfiguration.objects.filter(is_active=True).first()
        sender_field = 'whatsapp_number' # Make sure this matches your model field

    if config and sender_field:
        return getattr(config, sender_field, None)
    return None