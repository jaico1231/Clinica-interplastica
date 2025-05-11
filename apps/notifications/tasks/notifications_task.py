# notifications/tasks.py

import logging
from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from apps.notifications.models.emailmodel import MessageLog, EmailConfiguration, SMSConfiguration, ScheduledMessage, WhatsAppConfiguration
from apps.notifications.views.notifications_view import (
    send_email_via_backend,
    send_sms_via_backend,
    send_whatsapp_via_backend
)
# Import backend handlers (we'll create this next or define logic here)
# from .backends import (
#     send_email_via_backend,
#     send_sms_via_backend,
#     send_whatsapp_via_backend
# )

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60) # Example retry config
def process_notification_task(self, message_log_id: int):
    """
    Celery task to process and send a single notification.
    """
    try:
        log_entry = MessageLog.objects.get(pk=message_log_id)
    except ObjectDoesNotExist:
        logger.error(f"MessageLog with ID {message_log_id} not found. Task aborted.")
        return # Cannot proceed

    # Check if already processed or canceled
    if log_entry.status != MessageLog.MessageStatus.PENDING:
        logger.warning(f"MessageLog ID {message_log_id} is not PENDING (Status: {log_entry.status}). Task aborted.")
        return

    config = None
    send_function = None
    provider_name = "Unknown" # Default

    try:
        # Select appropriate configuration and backend function
        if log_entry.message_type == MessageLog.MessageType.EMAIL:
            config = EmailConfiguration.get_active_configuration()
            if not config: raise ValueError("No active Email configuration found.")
            provider_name = config.get_backend_display() # Get human-readable backend name
            send_function = send_email_via_backend

        elif log_entry.message_type == MessageLog.MessageType.SMS:
            config = SMSConfiguration.objects.filter(is_active=True).first()
            if not config: raise ValueError("No active SMS configuration found.")
            provider_name = config.get_backend_display()
            send_function = send_sms_via_backend

        elif log_entry.message_type == MessageLog.MessageType.WHATSAPP:
            config = WhatsAppConfiguration.objects.filter(is_active=True).first()
            if not config: raise ValueError("No active WhatsApp configuration found.")
            provider_name = config.get_backend_display()
            send_function = send_whatsapp_via_backend

        else:
            raise NotImplementedError(f"Message type '{log_entry.message_type}' not supported.")

        # --- Execute Sending ---
        logger.info(f"Attempting to send {log_entry.message_type} (ID: {log_entry.pk}) via {provider_name}...")
        # Pass config and log_entry to the backend function
        result = send_function(config, log_entry) # Backend function should return dict with status info

        # --- Update Log on Success ---
        log_entry.status = MessageLog.MessageStatus.SENT # Or DELIVERED if backend confirms
        log_entry.sent_at = timezone.now()
        log_entry.provider = provider_name
        log_entry.provider_message_id = result.get('provider_message_id')
        log_entry.error_message = None # Clear previous errors if any
        log_entry.retries = self.request.retries # Store current retry count
        log_entry.save(update_fields=[
            'status', 'sent_at', 'provider', 'provider_message_id', 'error_message', 'retries'
        ])
        logger.info(f"Successfully sent {log_entry.message_type} (ID: {log_entry.pk}). Provider ID: {log_entry.provider_message_id}")

    except Exception as e:
        logger.error(f"Failed to send {log_entry.message_type} (ID: {log_entry.pk}) on attempt {self.request.retries + 1}: {e}", exc_info=True)

        # --- Update Log on Failure ---
        log_entry.status = MessageLog.MessageStatus.FAILED
        log_entry.error_message = f"Attempt {self.request.retries + 1}: {e}"
        log_entry.retries = self.request.retries + 1
        log_entry.provider = provider_name # Log which provider failed
        log_entry.save(update_fields=['status', 'error_message', 'retries', 'provider'])

        # --- Retry Logic ---
        try:
            # Retry the task based on shared_task decorator config (max_retries, default_retry_delay)
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for MessageLog ID {log_entry.pk}. Marking as permanently FAILED.")
            # Status is already FAILED, no further action needed unless you want specific handling


# --- Task for Scheduled Messages ---
# You'll need a Celery Beat schedule to run this periodically (e.g., every minute)
@shared_task
def process_scheduled_messages():
    """
    Finds pending scheduled messages whose time has come and enqueues them.
    """
    now = timezone.now()
    # Find messages scheduled for now or earlier, not yet processed, and not canceled
    scheduled_items = ScheduledMessage.objects.filter(
        scheduled_time__lte=now,
        processed=False,
        canceled=False
    ).select_related('message_log') # Optimize query

    logger.info(f"Found {scheduled_items.count()} scheduled messages to process.")

    for item in scheduled_items:
        log_entry = item.message_log
        if log_entry.status == MessageLog.MessageStatus.PENDING:
            logger.info(f"Processing scheduled message ID: {item.pk}, Log ID: {log_entry.pk}")
            # Enqueue the actual sending task
            process_notification_task.delay(log_entry.pk)
            # Mark as processed (prevents re-sending by this task)
            item.processed = True
            item.last_run = now # Record when it was picked up
            # TODO: Handle recurrence - calculate next_run if applicable
            # if item.recurring:
            #     item.next_run = item.calculate_next_run() # Assumes calculate_next_run exists and works
            #     if item.next_run:
            #         item.processed = False # Reset processed if it needs to run again
            #     else: # No next run, recurrence ends
            #         logger.info(f"Recurrence ended for scheduled message ID: {item.pk}")

            item.save()
        else:
            # If the log status is not PENDING (e.g., FAILED from a previous attempt),
            # mark scheduled item as processed to avoid retrying indefinitely via scheduler.
            # The retry logic is handled within process_notification_task.
            logger.warning(f"Scheduled message ID {item.pk} linked to non-PENDING log (ID: {log_entry.pk}, Status: {log_entry.status}). Marking as processed.")
            item.processed = True
            item.save(update_fields=['processed'])