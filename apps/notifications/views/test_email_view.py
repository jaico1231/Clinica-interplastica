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
            
            # NUEVA VALIDACIÓN: Verificar si la contraseña está configurada
            if not password:
                error_message = _('No se ha proporcionado una contraseña. Para servidores SMTP como Hostinger la contraseña es obligatoria.')
                logger.warning(f"Error: {error_message}")
                
                # PRINT para depuración
                print("\n" + "!" * 80)
                print("ERROR: NO SE HA PROPORCIONADO CONTRASEÑA PARA CONEXIÓN SMTP")
                print("El servidor SMTP requiere autenticación y rechazará la conexión sin contraseña")
                print("!" * 80 + "\n")
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_message})
                else:
                    messages.error(request, error_message)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
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
                print(f"Longitud de contraseña: {len(password) if password else 0}")  # NUEVA LÍNEA
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
        
        # RESTO DEL CÓDIGO SIGUE IGUAL...
        # [Código para SENDGRID, SES y otros backends]
                
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