from django.core.mail import send_mail
send_mail('Asunto de prueba', 'Cuerpo de prueba', 'remitente@example.com', ['destinatario@example.com'])