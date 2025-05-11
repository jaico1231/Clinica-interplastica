# apps/notifications/views/test_email_view.py

import json
import socket
import logging
import smtplib
import traceback
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
from django.contrib import messages
from django.urls import reverse

from apps.notifications.models.emailmodel import EmailConfiguration
from apps.notifications.backend.email_backend import DatabaseEmailBackend

logger = logging.getLogger(__name__)

@login_required
@require_POST
def test_email_view(request):
    """
    Vista para enviar un correo electrónico de prueba utilizando 
    la configuración proporcionada por el formulario.
    Versión organizada que utiliza mensajes de Django y valida la configuración.
    """
    try:
        # Obtener datos del formulario
        form_data = request.POST.dict()
        
        # Verificar si la solicitud espera una respuesta JSON (AJAX) o una redirección
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Imprimir datos recibidos para debug (excluyendo datos sensibles)
        debug_data = {k: '******' if k in ['password', 'api_key'] else v for k, v in form_data.items()}
        logger.info("=" * 50)
        logger.info("SOLICITUD DE PRUEBA DE EMAIL RECIBIDA")
        logger.info(f"Datos del formulario: {debug_data}")
        logger.info("=" * 50)
        
        # PRINT DETALLADO: Datos recibidos en el formulario
        print("\n" + "=" * 80)
        print("DATOS RECIBIDOS EN FORMULARIO DE PRUEBA DE EMAIL:")
        for key, value in form_data.items():
            if key in ['password', 'api_key']:
                print(f"{key}: {'*' * 10}")
            else:
                print(f"{key}: {value}")
        print("=" * 80 + "\n")
        
        # Verificar campos obligatorios
        test_recipient = form_data.get('test_recipient')
        from_email = form_data.get('from_email')
        backend_type = form_data.get('backend')
        
        if not test_recipient:
            message = _('Se requiere un destinatario para el correo de prueba.')
            logger.warning(f"Error: {message}")
            
            if is_ajax:
                return JsonResponse({'success': False, 'error': message})
            else:
                messages.error(request, message)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        if not from_email:
            message = _('Se requiere un correo remitente (from_email) para la prueba.')
            logger.warning(f"Error: {message}")
            
            if is_ajax:
                return JsonResponse({'success': False, 'error': message})
            else:
                messages.error(request, message)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        if not backend_type:
            message = _('Se requiere seleccionar un tipo de backend para la prueba.')
            logger.warning(f"Error: {message}")
            
            if is_ajax:
                return JsonResponse({'success': False, 'error': message})
            else:
                messages.error(request, message)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        
        # Opción para prueba rápida (sin SMTP)
        use_console_backend = request.POST.get('use_console_backend') == 'true'
        
        # === VALIDACIÓN DE CONFIGURACIÓN ===
        # Imprimir claramente los datos que se usarán
        logger.info("=" * 50)
        logger.info(f"CONFIGURACIÓN DE PRUEBA:")
        logger.info(f"- Backend: {backend_type}")
        logger.info(f"- Destinatario: {test_recipient}")
        logger.info(f"- Remitente: {from_email}")
        logger.info(f"- Modo consola: {use_console_backend}")
        
        # === MODO CONSOLA (PARA PRUEBAS RÁPIDAS) ===
        if use_console_backend:
            logger.info("ENVIANDO EN MODO CONSOLA (SIN SERVIDOR REAL)")
            logger.info("=" * 50)
            
            # PRINT DETALLADO: Modo consola
            print("\n" + "*" * 80)
            print("ENVIANDO EN MODO CONSOLA (SIN CONEXIÓN REAL)")
            print(f"Remitente: {from_email}")
            print(f"Destinatario: {test_recipient}")
            print("*" * 80 + "\n")
            
            # Crear un mensaje de prueba simple
            subject = _("Correo de prueba - Modo Consola")
            message = _("""
            Este es un correo de prueba en modo consola. 
            NO SE ESTÁ UTILIZANDO EL SERVIDOR DE CORREO REAL.
            
            Destinatario: {recipient}
            Remitente: {sender}
            """).format(
                recipient=test_recipient,
                sender=from_email
            )
            
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email,
                to=[test_recipient],
                connection=ConsoleEmailBackend()
            )
            
            email.send()
            
            success_message = _('⚠️ PRUEBA EN MODO CONSOLA: No se envió un correo real. Revisa los logs del servidor para ver el contenido simulado.')
            logger.info(f"Éxito: {success_message}")
            
            if is_ajax:
                return JsonResponse({'success': True, 'message': success_message})
            else:
                messages.warning(request, success_message)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        
        # === ENVÍO REAL POR BACKEND ESPECÍFICO ===
        # SMTP
        if backend_type == EmailConfiguration.EmailBackend.SMTP:
            # Configuración directa de SMTP para pruebas
            host = form_data.get('host')
            port = int(form_data.get('port')) if form_data.get('port') else 587
            username = form_data.get('username')
            password = form_data.get('password')
            use_tls = form_data.get('security_protocol') in [
                EmailConfiguration.SecurityProtocol.TLS, 
                EmailConfiguration.SecurityProtocol.STARTTLS
            ]
            use_ssl = form_data.get('security_protocol') == EmailConfiguration.SecurityProtocol.SSL
            timeout = int(form_data.get('timeout', 30))
            
            # Validar y mostrar configuración SMTP
            logger.info(f"CONFIGURACIÓN SMTP:")
            logger.info(f"- Host: {host}")
            logger.info(f"- Puerto: {port}")
            logger.info(f"- Usuario: {username}")
            logger.info(f"- Contraseña: {'Configurada' if password else 'No configurada'}")
            logger.info(f"- TLS: {use_tls}")
            logger.info(f"- SSL: {use_ssl}")
            logger.info(f"- Timeout: {timeout}s")
            logger.info("=" * 50)
            
            if not host:
                message = _('Se requiere un host SMTP para realizar la prueba.')
                logger.warning(f"Error: {message}")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': message})
                else:
                    messages.error(request, message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
            try:
                # Probar conexión rápida primero
                logger.info(f"Intentando conexión básica a {host}:{port}...")
                
                # PRINT DETALLADO: Datos de conexión SMTP
                print("\n" + "*" * 80)
                print("DATOS DE CONEXIÓN SMTP:")
                print(f"Host: {host}")
                print(f"Puerto: {port}")
                print(f"Usuario: {username}")
                print(f"Contraseña configurada: {'Sí' if password else 'No'}")
                print(f"Use TLS: {use_tls}")
                print(f"Use SSL: {use_ssl}")
                print(f"Timeout: {timeout} segundos")
                print(f"Remitente: {from_email}")
                print(f"Destinatario: {test_recipient}")
                print("*" * 80 + "\n")
                
                # Probar socket primero para verificar conectividad básica
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)  # 5 segundos solo para la prueba de socket
                s.connect((host, port))
                s.close()
                
                logger.info(f"Conexión básica a {host}:{port} establecida.")
                
                # Crear backend SMTP
                connection = SMTPEmailBackend(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    use_tls=use_tls,
                    use_ssl=use_ssl,
                    timeout=timeout,
                    fail_silently=False
                )
                
                # Crear el mensaje de prueba
                subject = _("Correo de prueba - SMTP")
                message = _("""
                Este es un correo de prueba REAL enviado desde la configuración:
                
                Host: {host}
                Puerto: {port}
                Usuario: {username}
                Protocolo de seguridad: {security}
                
                Si has recibido este correo, la configuración funciona correctamente.
                """).format(
                    host=host or 'N/A',
                    port=port or 'N/A',
                    username=username or 'N/A',
                    security=form_data.get('security_protocol')
                )
                
                # Enviar el correo usando from_email
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=[test_recipient],
                    connection=connection
                )
                
                logger.info(f"Enviando email de prueba a {test_recipient}...")
                email.send(fail_silently=False)
                logger.info("Email enviado correctamente")
                
                success_message = _('✅ Correo de prueba enviado correctamente a {recipient} desde {sender}').format(
                    recipient=test_recipient,
                    sender=from_email
                )
                logger.info(f"Éxito: {success_message}")
                
                if is_ajax:
                    return JsonResponse({'success': True, 'message': success_message})
                else:
                    messages.success(request, success_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
            except socket.timeout as e:
                error_message = _('Tiempo de espera agotado al conectar con el servidor. Verifica que el servidor esté accesible y que el puerto no esté bloqueado.')
                logger.error(f"Error: {error_message} - {e}")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_message})
                else:
                    messages.error(request, error_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
            except socket.error as e:
                error_message = _('No se pudo establecer conexión con el servidor. Verifica la dirección y puerto: {error}').format(error=str(e))
                logger.error(f"Error: {error_message}")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_message})
                else:
                    messages.error(request, error_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
            except smtplib.SMTPAuthenticationError as e:
                error_message = _('Error de autenticación SMTP. Verifica tu nombre de usuario y contraseña.')
                logger.error(f"Error: {error_message} - {e}")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_message})
                else:
                    messages.error(request, error_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
            except smtplib.SMTPException as e:
                error_message = _('Error SMTP: {error}').format(error=str(e))
                logger.error(f"Error: {error_message}")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_message})
                else:
                    messages.error(request, error_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
        # SENDGRID
        elif backend_type == EmailConfiguration.EmailBackend.SENDGRID:
            # Importaciones y configuración específica para SendGrid
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            api_key = form_data.get('api_key')
            
            # Validar y mostrar configuración SendGrid
            logger.info(f"CONFIGURACIÓN SENDGRID:")
            logger.info(f"- API Key: {'Configurada' if api_key else 'No configurada'}")
            logger.info("=" * 50)
            
            if not api_key:
                error_message = _('Se requiere una API Key para probar el envío con SendGrid.')
                logger.warning(f"Error: {error_message}")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_message})
                else:
                    messages.error(request, error_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
            try:
                logger.info("Enviando correo con SendGrid...")
                
                # PRINT DETALLADO: Datos de conexión SendGrid
                print("\n" + "*" * 80)
                print("DATOS DE CONEXIÓN SENDGRID:")
                print(f"API Key configurada: {'Sí' if api_key else 'No'}")
                print(f"API Key (primeros 5 caracteres): {api_key[:5] + '...' if api_key and len(api_key) > 5 else 'N/A'}")
                print(f"Remitente: {from_email}")
                print(f"Destinatario: {test_recipient}")
                print("*" * 80 + "\n")
                
                # Crear el mensaje para SendGrid
                message = Mail(
                    from_email=from_email,
                    to_emails=[test_recipient],
                    subject=_("Correo de prueba - SendGrid"),
                    html_content=_("""
                    <h2>Prueba de configuración SendGrid</h2>
                    <p>Este es un correo de prueba REAL enviado utilizando SendGrid API.</p>
                    <p>Si has recibido este correo, la configuración funciona correctamente.</p>
                    """)
                )
                
                # Enviar utilizando SendGrid
                sendgrid_client = SendGridAPIClient(api_key=api_key)
                response = sendgrid_client.send(message)
                
                logger.info(f"Respuesta de SendGrid: código {response.status_code}")
                
                if response.status_code >= 200 and response.status_code < 300:
                    success_message = _('✅ Correo de prueba enviado correctamente a {recipient} desde {sender} usando SendGrid').format(
                        recipient=test_recipient,
                        sender=from_email
                    )
                    logger.info(f"Éxito: {success_message}")
                    
                    if is_ajax:
                        return JsonResponse({'success': True, 'message': success_message})
                    else:
                        messages.success(request, success_message)
                        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                else:
                    error_message = _('Error al enviar correo con SendGrid. Código: {status_code}').format(
                        status_code=response.status_code
                    )
                    logger.error(f"Error: {error_message}")
                    
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': error_message})
                    else:
                        messages.error(request, error_message)
                        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                    
            except Exception as e:
                error_message = _('Error al enviar correo con SendGrid: {error}').format(error=str(e))
                logger.exception(f"Error: {error_message}")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_message})
                else:
                    messages.error(request, error_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
        # AMAZON SES
        elif backend_type == EmailConfiguration.EmailBackend.SES:
            # Importaciones y configuración específica para Amazon SES
            import boto3
            from botocore.exceptions import ClientError
            
            aws_access_key = form_data.get('aws_access_key') or form_data.get('username')
            aws_secret_key = form_data.get('aws_secret_key') or form_data.get('password')
            region = form_data.get('region') or form_data.get('api_key') or 'us-east-1'
            
            # Validar y mostrar configuración SES
            logger.info(f"CONFIGURACIÓN AMAZON SES:")
            logger.info(f"- Región: {region}")
            logger.info(f"- Access Key: {'Configurada' if aws_access_key else 'No configurada'}")
            logger.info(f"- Secret Key: {'Configurada' if aws_secret_key else 'No configurada'}")
            logger.info("=" * 50)
            
            if not aws_access_key or not aws_secret_key:
                error_message = _('Se requieren las credenciales de AWS para probar el envío con Amazon SES.')
                logger.warning(f"Error: {error_message}")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_message})
                else:
                    messages.error(request, error_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
            try:
                logger.info(f"Enviando correo con Amazon SES...")
                
                # PRINT DETALLADO: Datos de conexión Amazon SES
                print("\n" + "*" * 80)
                print("DATOS DE CONEXIÓN AMAZON SES:")
                print(f"Región: {region}")
                print(f"Access Key configurada: {'Sí' if aws_access_key else 'No'}")
                print(f"Access Key (primeros 5 caracteres): {aws_access_key[:5] + '...' if aws_access_key and len(aws_access_key) > 5 else 'N/A'}")
                print(f"Secret Key configurada: {'Sí' if aws_secret_key else 'No'}")
                print(f"Remitente: {from_email}")
                print(f"Destinatario: {test_recipient}")
                print("*" * 80 + "\n")
                
                # Crear cliente de SES
                ses_client = boto3.client(
                    'ses',
                    region_name=region,
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key
                )
                
                # Enviar el correo de prueba
                response = ses_client.send_email(
                    Source=from_email,
                    Destination={
                        'ToAddresses': [test_recipient],
                    },
                    Message={
                        'Subject': {
                            'Data': _("Correo de prueba - Amazon SES"),
                            'Charset': 'UTF-8'
                        },
                        'Body': {
                            'Text': {
                                'Data': _("Este es un correo de prueba REAL enviado desde Amazon SES. Si has recibido este correo, la configuración funciona correctamente."),
                                'Charset': 'UTF-8'
                            },
                            'Html': {
                                'Data': _("<h2>Prueba de configuración Amazon SES</h2><p>Este es un correo de prueba REAL enviado utilizando Amazon SES API.</p><p>Si has recibido este correo, la configuración funciona correctamente.</p>"),
                                'Charset': 'UTF-8'
                            }
                        }
                    }
                )
                
                message_id = response.get('MessageId', 'Unknown')
                logger.info(f"Correo enviado con SES. Message ID: {message_id}")
                
                success_message = _('✅ Correo de prueba enviado correctamente a {recipient} desde {sender} usando Amazon SES (ID: {message_id})').format(
                    recipient=test_recipient,
                    sender=from_email,
                    message_id=message_id
                )
                logger.info(f"Éxito: {success_message}")
                
                if is_ajax:
                    return JsonResponse({'success': True, 'message': success_message})
                else:
                    messages.success(request, success_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                error_display = _('Error AWS SES: {code} - {message}').format(
                    code=error_code,
                    message=error_message
                )
                logger.error(f"Error: {error_display}")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_display})
                else:
                    messages.error(request, error_display)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
            except Exception as e:
                error_message = _('Error al enviar correo con Amazon SES: {error}').format(error=str(e))
                logger.exception(f"Error: {error_message}")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_message})
                else:
                    messages.error(request, error_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
        # OTROS BACKENDS (DatabaseEmailBackend)
        else:
            # Intentamos usar el backend de base de datos con configuración temporal
            logger.info(f"CONFIGURACIÓN BACKEND DINÁMICO ({backend_type}):")
            logger.info(f"- Host: {form_data.get('host')}")
            logger.info(f"- Puerto: {form_data.get('port')}")
            logger.info(f"- Usuario: {form_data.get('username')}")
            logger.info(f"- Contraseña: {'Configurada' if form_data.get('password') else 'No configurada'}")
            logger.info(f"- API Key: {'Configurada' if form_data.get('api_key') else 'No configurada'}")
            logger.info(f"- Protocolo: {form_data.get('security_protocol')}")
            logger.info("=" * 50)
            
            try:
                # PRINT DETALLADO: Datos de conexión Backend Dinámico
                print("\n" + "*" * 80)
                print(f"DATOS DE CONEXIÓN PARA BACKEND DINÁMICO ({backend_type}):")
                print(f"Backend: {backend_type}")
                print(f"Host: {form_data.get('host', 'N/A')}")
                print(f"Puerto: {form_data.get('port', 'N/A')}")
                print(f"Usuario: {form_data.get('username', 'N/A')}")
                print(f"Contraseña configurada: {'Sí' if form_data.get('password') else 'No'}")
                print(f"API Key configurada: {'Sí' if form_data.get('api_key') else 'No'}")
                print(f"Protocolo: {form_data.get('security_protocol', 'N/A')}")
                print(f"Timeout: {form_data.get('timeout', '30')} segundos")
                print(f"Remitente: {from_email}")
                print(f"Destinatario: {test_recipient}")
                print("*" * 80 + "\n")
                
                # Crear una configuración temporal basada en los datos del formulario
                temp_config = EmailConfiguration(
                    name="Configuración Temporal",
                    backend=backend_type,
                    from_email=from_email,
                    host=form_data.get('host'),
                    port=form_data.get('port'),
                    username=form_data.get('username'),
                    password=form_data.get('password'),
                    api_key=form_data.get('api_key'),
                    security_protocol=form_data.get('security_protocol', EmailConfiguration.SecurityProtocol.TLS),
                    timeout=int(form_data.get('timeout', 30)),
                    is_active=True
                )
                
                # Crear backend y establecer la configuración
                logger.info("Creando instancia de DatabaseEmailBackend con configuración temporal")
                backend = DatabaseEmailBackend(fail_silently=False)
                backend.config = temp_config
                
                # PRINT adicional de la configuración del backend dinámico
                print("\n" + "*" * 80)
                print("CONFIGURACIÓN TEMPORAL CREADA PARA BACKEND DINÁMICO:")
                print(f"Nombre: {temp_config.name}")
                print(f"Backend: {temp_config.backend}")
                print(f"Host: {temp_config.host}")
                print(f"Puerto: {temp_config.port}")
                print(f"Usuario: {temp_config.username}")
                print(f"Contraseña configurada: {'Sí' if temp_config.password else 'No'}")
                print(f"API Key configurada: {'Sí' if temp_config.api_key else 'No'}")
                print(f"Protocolo: {temp_config.security_protocol}")
                print(f"Timeout: {temp_config.timeout}")
                print(f"From Email: {temp_config.from_email}")
                print("*" * 80 + "\n")
                
                # Crear mensaje
                subject = _("Correo de prueba - Backend Dinámico")
                message = _("""
                Este es un correo de prueba REAL enviado usando el backend dinámico.
                
                Backend: {backend}
                Destinatario: {recipient}
                Remitente: {sender}
                
                Si has recibido este correo, la configuración funciona correctamente.
                """).format(
                    backend=backend_type,
                    recipient=test_recipient,
                    sender=from_email
                )
                
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=[test_recipient],
                    connection=backend
                )
                
                logger.info(f"Enviando email con backend dinámico a {test_recipient}...")
                email.send(fail_silently=False)
                logger.info("Email enviado correctamente")
                
                success_message = _('✅ Correo de prueba enviado correctamente a {recipient} usando el backend {backend}').format(
                    recipient=test_recipient,
                    backend=backend_type
                )
                logger.info(f"Éxito: {success_message}")
                
                if is_ajax:
                    return JsonResponse({'success': True, 'message': success_message})
                else:
                    messages.success(request, success_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
            except Exception as e:
                logger.exception(f"Error al enviar correo con backend dinámico: {e}")
                
                # PRINT DETALLADO: Error en backend dinámico
                print("\n" + "*" * 80)
                print(f"ERROR EN BACKEND DINÁMICO ({backend_type}):")
                print(f"Error: {str(e)}")
                print(f"Tipo de error: {type(e).__name__}")
                print(f"Traceback:\n{traceback.format_exc()}")
                print("*" * 80 + "\n")
                
                # Fallback al modo consola con advertencia
                logger.warning(f"Fallando a modo consola después de error con backend {backend_type}")
                
                email = EmailMessage(
                    subject=_("Correo de prueba - Modo Consola (Fallback)"),
                    body=_("""
                    ⚠️ MODO CONSOLA DE RESPALDO
                    
                    Se intentó enviar un correo real con el backend {backend} pero falló:
                    Error: {error}
                    
                    Este es un mensaje de respaldo usando el modo consola.
                    Destinatario: {recipient}
                    Remitente: {sender}
                    """).format(
                        backend=backend_type,
                        error=str(e),
                        recipient=test_recipient,
                        sender=from_email
                    ),
                    from_email=from_email,
                    to=[test_recipient],
                    connection=ConsoleEmailBackend()
                )
                
                email.send()
                
                error_message = _('No se pudo enviar correo real con el backend {backend}: {error}').format(
                    backend=backend_type,
                    error=str(e)
                )
                logger.error(f"Error: {error_message}")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_message})
                else:
                    messages.error(request, error_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.exception(f"Error no manejado al enviar correo: {e}")
        logger.debug(f"Detalles del error: {error_details}")
        
        # PRINT DETALLADO: Error general no manejado
        print("\n" + "*" * 80)
        print("ERROR NO MANEJADO EN TEST_EMAIL_VIEW:")
        print(f"Error: {str(e)}")
        print(f"Tipo: {type(e).__name__}")
        print(f"Traceback:\n{error_details}")
        print("*" * 80 + "\n")
        
        error_message = _('Error al enviar correo: {error}. Revisa los logs del servidor para más detalles.').format(
            error=str(e)
        )
        
        if is_ajax:
            return JsonResponse({'success': False, 'error': error_message}, status=500)
        else:
            messages.error(request, error_message)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))