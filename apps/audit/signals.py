# signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from django.conf import settings
from django.contrib.auth import user_logged_in, user_logged_out
from django.db.models import Model
import json
import threading

from apps.audit.models import AuditLog

# Variable local de thread para almacenar datos temporales entre señales
thread_local = threading.local()

class AuditableModelMixin:
    """
    Mixin para añadir a modelos que queremos auditar
    """
    # Lista de campos a excluir de la auditoría, por ejemplo, campos sensibles
    audit_exclude = []
    
    # Si es False, no se auditará el modelo. Útil para deshabilitar temporalmente
    audit_enabled = True

def get_client_ip(request):
    """Obtiene la dirección IP del cliente desde la solicitud"""
    if not request:
        return None
        
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_agent(request):
    """Obtiene el user agent del cliente desde la solicitud"""
    if not request:
        return None
        
    return request.META.get('HTTP_USER_AGENT', '')

def get_serialized_data(instance, exclude_fields=None):
    """
    Serializa los datos de un modelo para almacenarlos en el registro de auditoría
    """
    if exclude_fields is None:
        exclude_fields = getattr(instance, 'audit_exclude', [])
    
    # Agregar campos sensibles predeterminados
    exclude_fields.extend(['password', 'token', 'secret', 'key'])
    
    data = {}
    
    # Obtener todos los campos del modelo
    for field in instance._meta.fields:
        field_name = field.name
        
        # Excluir campos específicos
        if field_name in exclude_fields:
            continue
        
        # Obtener valor del campo
        value = getattr(instance, field_name)
        
        # Convertir a un formato serializable
        if value is not None:
            if hasattr(value, 'pk'):
                # Si es una relación, guardar solo la clave primaria
                data[field_name] = value.pk
            else:
                try:
                    # Intentar serializar directamente
                    json.dumps({field_name: value})
                    data[field_name] = value
                except (TypeError, OverflowError):
                    # Si no es serializable, convertir a string
                    data[field_name] = force_str(value)
    
    return data

def should_audit_model(model_instance_or_class):
    """
    Determina si un modelo debe ser auditado basado en la configuración
    """
    # Si es una instancia, obtener su clase
    if isinstance(model_instance_or_class, Model):
        model_class = model_instance_or_class.__class__
    else:
        model_class = model_instance_or_class
    
    # Verificar si el modelo hereda de AuditableModelMixin
    if isinstance(model_instance_or_class, AuditableModelMixin):
        if not getattr(model_instance_or_class, 'audit_enabled', True):
            return False
        return True
    
    # Verificar si el modelo está en AUDIT_MODELS
    model_path = f"{model_class._meta.app_label}.{model_class.__name__}"
    return model_path in getattr(settings, 'AUDIT_MODELS', [])

@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    """Captura el estado anterior antes de guardar"""
    # Evitar auditar el modelo AuditLog para prevenir recursión
    if sender == AuditLog:
        return
        
    # Verificar si el modelo debe ser auditado
    if not should_audit_model(instance):
        return
    
    # Si es una instancia nueva, no hay estado anterior
    if not instance.pk:
        return
    
    try:
        # Obtener la instancia antes de modificarse
        previous = sender.objects.get(pk=instance.pk)
        thread_local.previous_data = get_serialized_data(previous)
    except sender.DoesNotExist:
        thread_local.previous_data = {}
    except Exception as e:
        # Capturar cualquier error para evitar interrumpir el flujo normal
        print(f"Error al obtener datos anteriores: {e}")
        thread_local.previous_data = {}

@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """
    Registra eventos de creación y actualización
    """
    # Evitar auditar el modelo AuditLog para prevenir recursión
    if sender == AuditLog:
        return
        
    # Verificar si el modelo debe ser auditado
    if not should_audit_model(instance):
        return
    
    try:
        # Obtener los datos actuales
        current_data = get_serialized_data(instance)
        
        # Determinar si es creación o actualización
        action = 'CREATE' if created else 'UPDATE'
        
        # Obtener datos anteriores (solo para actualizaciones)
        previous_data = getattr(thread_local, 'previous_data', {}) if not created else {}
        
        # Si no hay cambios en los datos (para actualizaciones), evitar registro
        if action == 'UPDATE' and previous_data == current_data:
            return
        
        # Obtener el usuario actual desde el contexto (si está disponible)
        user = getattr(thread_local, 'request_user', None)
        
        # Crear registro de auditoría
        content_type = ContentType.objects.get_for_model(sender)
        
        # Obtener información de la solicitud si está disponible
        request = getattr(thread_local, 'request', None)
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        # Crear el registro
        AuditLog.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            object_id=str(instance.pk),
            table_name=sender._meta.db_table,
            data_before=previous_data if action == 'UPDATE' else None,
            data_after=current_data,
            ip_address=ip_address,
            user_agent=user_agent,
            description=f"{action} en {sender._meta.verbose_name}: {instance}"
        )
    except Exception as e:
        # Capturar cualquier error para evitar interrumpir la operación principal
        print(f"Error al registrar auditoría: {e}")
    finally:
        # Limpiar datos almacenados
        if hasattr(thread_local, 'previous_data'):
            del thread_local.previous_data

@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """
    Registra eventos de eliminación
    """
    # Evitar auditar el modelo AuditLog para prevenir recursión
    if sender == AuditLog:
        return
        
    # Verificar si el modelo debe ser auditado
    if not should_audit_model(instance):
        return
    
    try:
        # Obtener datos antes de eliminación
        previous_data = get_serialized_data(instance)
        
        # Obtener el usuario actual desde el contexto (si está disponible)
        user = getattr(thread_local, 'request_user', None)
        
        # Crear registro de auditoría
        content_type = ContentType.objects.get_for_model(sender)
        
        # Obtener información de la solicitud si está disponible
        request = getattr(thread_local, 'request', None)
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        AuditLog.objects.create(
            user=user,
            action='DELETE',
            content_type=content_type,
            object_id=str(instance.pk),
            table_name=sender._meta.db_table,
            data_before=previous_data,
            data_after=None,
            ip_address=ip_address,
            user_agent=user_agent,
            description=f"DELETE en {sender._meta.verbose_name}: {instance}"
        )
    except Exception as e:
        # Capturar cualquier error para evitar interrumpir la operación principal
        print(f"Error al registrar auditoría de eliminación: {e}")

# Registrar eventos de inicio y cierre de sesión
@receiver(user_logged_in)
def audit_user_login(sender, request, user, **kwargs):
    """Registra eventos de inicio de sesión"""
    try:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        AuditLog.objects.create(
            user=user,
            action='LOGIN',
            ip_address=ip_address,
            user_agent=user_agent,
            description=f"Inicio de sesión: {user.username}"
        )
    except Exception as e:
        print(f"Error al registrar inicio de sesión: {e}")

@receiver(user_logged_out)
def audit_user_logout(sender, request, user, **kwargs):
    """Registra eventos de cierre de sesión"""
    try:
        if user:  # A veces user puede ser None
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
            
            AuditLog.objects.create(
                user=user,
                action='LOGOUT',
                ip_address=ip_address,
                user_agent=user_agent,
                description=f"Cierre de sesión: {user.username}"
            )
    except Exception as e:
        print(f"Error al registrar cierre de sesión: {e}")
