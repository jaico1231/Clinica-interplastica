# notifications/mixins.py
from apps.notifications.services.notifications_services import send_notification
from apps.notifications.models.emailmodel import MessageLog

class NotificationMixin:
    notification_message_type = None # e.g., MessageLog.MessageType.EMAIL
    notification_template_name = None
    notification_recipient_field = 'email' # Field name on the object being saved/processed
    notification_subject = None # Or method name to get subject
    # ... other options

    def send_object_notification(self, obj, context_override=None):
        if not self.notification_message_type or not self.notification_template_name:
            # Log warning or raise error
            return

        recipient = getattr(obj, self.notification_recipient_field, None)
        if not recipient:
             # Log warning or raise error
             return

        context = self.get_notification_context(obj)
        if context_override:
            context.update(context_override)

        subject = self.get_notification_subject(obj)

        try:
            send_notification(
                message_type=self.notification_message_type,
                recipient=recipient,
                template_name=self.notification_template_name,
                context=context,
                subject=subject,
                # ... pass other relevant params
            )
        except Exception as e:
            # Log error
            pass # Decide how to handle failures

    def get_notification_context(self, obj):
        # Default context, override in view if needed
        return {'object': obj, 'user': getattr(self, 'request', None).user if hasattr(self, 'request') else None}

    def get_notification_subject(self, obj):
         # Default subject, override in view if needed
         return self.notification_subject

# Ejemplo de uso en una CreateView
# class UserCreateView(LoginRequiredMixin, NotificationMixin, CreateView):
#     model = User
#     form_class = UserCreationForm
#     template_name = '...'
#     success_url = '...'
#
#     # Configure the mixin
#     notification_message_type = MessageLog.MessageType.EMAIL
#     notification_template_name = 'welcome_email'
#     notification_recipient_field = 'email'
#     notification_subject = "Welcome to Our Platform!"
#
#     def form_valid(self, form):
#         response = super().form_valid(form)
#         # Send notification after object is saved
#         self.send_object_notification(self.object)
#         return response