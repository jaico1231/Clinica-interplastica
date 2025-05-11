# messaging/services.py

from django.core.mail import EmailMessage, get_connection as get_email_connection
from django.conf import settings
from django.template.loader import render_to_string
import logging
import json

from notifications.models.emailmodel import EmailConfiguration, SMSConfiguration, WhatsAppConfiguration

# Import necessary models
# from .models import EmailConfiguration, SMSConfiguration, WhatsAppConfiguration

logger = logging.getLogger(__name__)

class MessagingService:
    """
    Generic service for sending messages via different channels (Email, SMS, WhatsApp)
    """
    
    @staticmethod
    def send_email(
        subject, 
        message, 
        recipient_list, 
        from_email=None, 
        html_message=None, 
        attachments=None, 
        cc=None, 
        bcc=None, 
        config=None,
        template=None,
        context=None
    ):
        """
        Send an email using the active email configuration
        
        Args:
            subject (str): Email subject
            message (str): Plain text message content
            recipient_list (list): List of recipient email addresses
            from_email (str, optional): Sender email address (uses default if not provided)
            html_message (str, optional): HTML version of the message
            attachments (list, optional): List of attachment tuples (filename, content, mimetype)
            cc (list, optional): List of CC email addresses
            bcc (list, optional): List of BCC email addresses
            config (EmailConfiguration, optional): Specific config to use (uses active config if None)
            template (str, optional): Template name for rendering message
            context (dict, optional): Context data for template rendering
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Get email configuration (active one if not specified)
            if not config:
                config = EmailConfiguration.get_active_configuration()
                
            if not config:
                logger.error("No active email configuration found")
                return False
                
            # Get connection parameters
            connection_params = config.connection_params
            
            # Set backend based on configuration
            backend_path = 'django.core.mail.backends.smtp.EmailBackend'  # Default
            
            if config.backend == EmailConfiguration.EmailBackend.SENDGRID:
                backend_path = 'django.core.mail.backends.smtp.EmailBackend'  # SendGrid uses SMTP
            elif config.backend == EmailConfiguration.EmailBackend.SES:
                backend_path = 'django_ses.SESBackend'
            elif config.backend == EmailConfiguration.EmailBackend.CONSOLE:
                backend_path = 'django.core.mail.backends.console.EmailBackend'
            elif config.backend == EmailConfiguration.EmailBackend.FILE:
                backend_path = 'django.core.mail.backends.filebased.EmailBackend'
                connection_params['file_path'] = settings.EMAIL_FILE_PATH
                
            connection = get_email_connection(
                backend=backend_path,
                **connection_params
            )
            
            # Set from_email if not provided
            if not from_email:
                from_email = config.from_email
                
            # Render template if provided
            if template and context:
                message = render_to_string(f"{template}.txt", context)
                if html_message is None and template:  # Only override if not explicitly provided
                    try:
                        html_message = render_to_string(f"{template}.html", context)
                    except:
                        pass  # No HTML template available, using text version only
            
            # Create email message object
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list,
                cc=cc,
                bcc=bcc,
                connection=connection
            )
            
            # Set HTML content if provided
            if html_message:
                email.content_subtype = "html"
                email.body = html_message
                
            # Add custom headers if configured
            if config.use_custom_headers and config.custom_headers:
                for key, value in config.custom_headers.items():
                    email.extra_headers[key] = value
                    
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    filename, content, mimetype = attachment
                    email.attach(filename, content, mimetype)
                    
            # Send email
            sent_count = email.send(fail_silently=config.fail_silently)
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            if not config or not config.fail_silently:
                raise
            return False
    
    @staticmethod
    def send_sms(
        message, 
        recipient_number, 
        config=None, 
        sender=None
    ):
        """
        Send SMS using the active SMS configuration
        
        Args:
            message (str): SMS message content
            recipient_number (str): Recipient phone number in international format
            config (SMSConfiguration, optional): Specific config to use (uses active if None)
            sender (str, optional): Sender phone number (overrides config default)
            
        Returns:
            dict: Response from the SMS provider
        """
        try:
            # Get SMS configuration
            if not config:
                config = SMSConfiguration.objects.filter(is_active=True).first()
                
            if not config:
                logger.error("No active SMS configuration found")
                return {"success": False, "error": "No active SMS configuration"}
                
            # Get connection parameters
            conn_params = config.connection_params
            sender_number = sender or config.phone_number
            
            # Send SMS based on backend
            if config.backend == SMSConfiguration.SMSBackend.TWILIO:
                return MessagingService._send_twilio_sms(
                    message, 
                    recipient_number, 
                    sender_number, 
                    conn_params
                )
                
            elif config.backend == SMSConfiguration.SMSBackend.AWS_SNS:
                return MessagingService._send_aws_sns_sms(
                    message, 
                    recipient_number, 
                    conn_params
                )
                
            elif config.backend == SMSConfiguration.SMSBackend.PLIVO:
                return MessagingService._send_plivo_sms(
                    message, 
                    recipient_number, 
                    sender_number, 
                    conn_params
                )
                
            elif config.backend == SMSConfiguration.SMSBackend.NEXMO:
                return MessagingService._send_nexmo_sms(
                    message, 
                    recipient_number, 
                    sender_number, 
                    conn_params
                )
                
            elif config.backend == SMSConfiguration.SMSBackend.DEBUG:
                logger.info(f"DEBUG SMS: To: {recipient_number}, From: {sender_number}, Message: {message}")
                return {"success": True, "debug": True}
                
            else:
                logger.error(f"Unsupported SMS backend: {config.backend}")
                return {"success": False, "error": "Unsupported SMS backend"}
                
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def send_whatsapp(
        message, 
        recipient_number, 
        config=None, 
        media_url=None, 
        template_name=None, 
        template_params=None
    ):
        """
        Send WhatsApp message using the active WhatsApp configuration
        
        Args:
            message (str): Message content
            recipient_number (str): Recipient phone number in international format
            config (WhatsAppConfiguration, optional): Specific config to use (uses active if None)
            media_url (str, optional): URL to media to include in message
            template_name (str, optional): Template name for template messages
            template_params (dict, optional): Parameters for template
            
        Returns:
            dict: Response from the WhatsApp provider
        """
        try:
            # Get WhatsApp configuration
            if not config:
                config = WhatsAppConfiguration.objects.filter(is_active=True).first()
                
            if not config:
                logger.error("No active WhatsApp configuration found")
                return {"success": False, "error": "No active WhatsApp configuration"}
                
            # Get connection parameters
            conn_params = config.connection_params
            sender_number = config.whatsapp_number
            
            # Send WhatsApp message based on backend
            if config.backend == WhatsAppConfiguration.WhatsAppBackend.TWILIO:
                return MessagingService._send_twilio_whatsapp(
                    message, 
                    recipient_number, 
                    sender_number, 
                    conn_params, 
                    media_url
                )
                
            elif config.backend == WhatsAppConfiguration.WhatsAppBackend.META:
                return MessagingService._send_meta_whatsapp(
                    message, 
                    recipient_number, 
                    conn_params, 
                    template_name, 
                    template_params, 
                    media_url
                )
                
            elif config.backend == WhatsAppConfiguration.WhatsAppBackend.DEBUG:
                logger.info(f"DEBUG WHATSAPP: To: {recipient_number}, From: {sender_number}, Message: {message}")
                return {"success": True, "debug": True}
                
            else:
                logger.error(f"Unsupported WhatsApp backend: {config.backend}")
                return {"success": False, "error": "Unsupported WhatsApp backend"}
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {"success": False, "error": str(e)}

    # Implementation for specific backend providers
    @staticmethod
    def _send_twilio_sms(message, recipient_number, sender_number, conn_params):
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            client = Client(conn_params['account_sid'], conn_params['auth_token'])
            response = client.messages.create(
                body=message,
                from_=sender_number,
                to=recipient_number
            )
            
            return {
                "success": True,
                "message_sid": response.sid,
                "status": response.status
            }
            
        except ImportError:
            logger.error("Twilio library not installed")
            return {"success": False, "error": "Twilio library not installed"}
        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _send_aws_sns_sms(message, recipient_number, conn_params):
        """Send SMS via AWS SNS"""
        try:
            import boto3
            
            sns = boto3.client(
                'sns',
                region_name=conn_params['region'],
                aws_access_key_id=conn_params.get('account_sid'),
                aws_secret_access_key=conn_params.get('api_key')
            )
            
            response = sns.publish(
                PhoneNumber=recipient_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            
            return {
                "success": True,
                "message_id": response['MessageId']
            }
            
        except ImportError:
            logger.error("Boto3 library not installed")
            return {"success": False, "error": "Boto3 library not installed"}
        except Exception as e:
            logger.error(f"AWS SNS SMS error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _send_plivo_sms(message, recipient_number, sender_number, conn_params):
        """Send SMS via Plivo"""
        try:
            import plivo
            
            client = plivo.RestClient(conn_params['account_sid'], conn_params['auth_token'])
            response = client.messages.create(
                src=sender_number,
                dst=recipient_number,
                text=message
            )
            
            return {
                "success": True,
                "message_uuid": response['message_uuid'][0]
            }
            
        except ImportError:
            logger.error("Plivo library not installed")
            return {"success": False, "error": "Plivo library not installed"}
        except Exception as e:
            logger.error(f"Plivo SMS error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _send_nexmo_sms(message, recipient_number, sender_number, conn_params):
        """Send SMS via Vonage/Nexmo"""
        try:
            import vonage
            
            client = vonage.Client(
                key=conn_params['account_sid'],
                secret=conn_params['auth_token']
            )
            sms = vonage.Sms(client)
            
            response = sms.send_message({
                'from': sender_number,
                'to': recipient_number,
                'text': message
            })
            
            return {
                "success": response['messages'][0]['status'] == '0',
                "message_id": response['messages'][0]['message-id']
            }
            
        except ImportError:
            logger.error("Vonage library not installed")
            return {"success": False, "error": "Vonage library not installed"}
        except Exception as e:
            logger.error(f"Vonage/Nexmo SMS error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _send_twilio_whatsapp(message, recipient_number, sender_number, conn_params, media_url=None):
        """Send WhatsApp message via Twilio"""
        try:
            from twilio.rest import Client
            
            client = Client(conn_params['account_sid'], conn_params['auth_token'])
            
            # Format WhatsApp number for Twilio
            from_whatsapp = f"whatsapp:{sender_number}"
            to_whatsapp = f"whatsapp:{recipient_number}"
            
            params = {
                'body': message,
                'from_': from_whatsapp,
                'to': to_whatsapp
            }
            
            if media_url:
                params['media_url'] = [media_url]
                
            response = client.messages.create(**params)
            
            return {
                "success": True,
                "message_sid": response.sid,
                "status": response.status
            }
            
        except ImportError:
            logger.error("Twilio library not installed")
            return {"success": False, "error": "Twilio library not installed"}
        except Exception as e:
            logger.error(f"Twilio WhatsApp error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _send_meta_whatsapp(message, recipient_number, conn_params, template_name=None, template_params=None, media_url=None):
        """Send WhatsApp message via Meta Business API"""
        try:
            import requests
            
            business_id = conn_params['business_id']
            api_version = conn_params.get('api_version', 'v15.0')
            access_token = conn_params.get('auth_token')
            phone_number_id = conn_params.get('whatsapp_number')
            
            url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            # Prepare payload based on message type
            if template_name:
                # Template message
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": recipient_number,
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {"code": "en_US"},
                    }
                }
                
                # Add template parameters if provided
                if template_params:
                    components = []
                    if isinstance(template_params, list):
                        # List of parameters for template
                        components.append({
                            "type": "body",
                            "parameters": [{"type": "text", "text": param} for param in template_params]
                        })
                    elif isinstance(template_params, dict):
                        # More complex template structure
                        for component_type, params in template_params.items():
                            components.append({
                                "type": component_type,
                                "parameters": params
                            })
                    
                    if components:
                        payload["template"]["components"] = components
            else:
                # Regular text message
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": recipient_number,
                    "type": "text",
                    "text": {"body": message}
                }
                
                # Add media if provided
                if media_url:
                    # Determine media type from URL
                    media_type = "image"  # Default
                    if media_url.lower().endswith(('.mp4', '.mov')):
                        media_type = "video"
                    elif media_url.lower().endswith(('.pdf')):
                        media_type = "document"
                        
                    payload = {
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": recipient_number,
                        "type": media_type,
                        media_type: {"link": media_url}
                    }
            
            # Send request
            response = requests.post(url, headers=headers, json=payload, timeout=conn_params.get('timeout', 15))
            response_data = response.json()
            
            # Check for success
            if response.status_code == 200:
                return {
                    "success": True,
                    "message_id": response_data.get('messages', [{}])[0].get('id')
                }
            else:
                return {
                    "success": False,
                    "error": response_data.get('error', {}).get('message', 'Unknown error')
                }
                
        except ImportError:
            logger.error("Requests library not installed")
            return {"success": False, "error": "Requests library not installed"}
        except Exception as e:
            logger.error(f"Meta WhatsApp error: {str(e)}")
            return {"success": False, "error": str(e)}