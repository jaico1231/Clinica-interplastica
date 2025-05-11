

def send_test_sms(configuration, phone_number, message):
    """
    Envía un SMS de prueba utilizando la configuración proporcionada.
    
    Args:
        configuration (SMSConfiguration): La configuración SMS a utilizar
        phone_number (str): El número de teléfono del destinatario
        message (str): El texto del mensaje
        
    Returns:
        dict: Un diccionario con el resultado de la operación
    """
    if not configuration.is_active:
        return {'success': False, 'error': 'Esta configuración SMS no está activa'}
    
    try:
        # Dependiendo del backend, usar diferente lógica para enviar SMS
        if configuration.backend == 'twilio':
            # Importar cliente Twilio
            from twilio.rest import Client
            
            # Inicializar cliente Twilio
            client = Client(configuration.account_sid, configuration.auth_token)
            
            # Enviar el mensaje
            twilio_message = client.messages.create(
                body=message,
                from_=configuration.phone_number,
                to=phone_number
            )
            
            return {
                'success': True, 
                'message_id': twilio_message.sid
            }
            
        elif configuration.backend == 'aws_sns':
            # Importar boto3 para AWS SNS
            import boto3
            
            # Inicializar cliente AWS SNS
            sns = boto3.client(
                'sns',
                region_name=configuration.region,
                aws_access_key_id=configuration.account_sid,
                aws_secret_access_key=configuration.auth_token
            )
            
            # Enviar el mensaje
            response = sns.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': configuration.name[:11]  # SenderID puede tener máximo 11 caracteres
                    }
                }
            )
            
            return {
                'success': True, 
                'message_id': response['MessageId']
            }
            
        # Agregar más backends según sea necesario
        else:
            return {'success': False, 'error': f'Backend no soportado: {configuration.backend}'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}