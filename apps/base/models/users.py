#opcion B:
import re
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from apps.base.models.support import City, Country, DocType, State, ThemeType
from apps.base.models.basemodel import BaseModel
from django.templatetags.static import static


def Cargar_imagenes_articulos_path(instance, filename):
    # Obtener el número de documento del tercero
    identificacion = instance.identification_number
    # Reemplazar espacios en blanco por guiones bajos y eliminar caracteres especiales
    identificacion = re.sub(r'\W+', '_', str(identificacion))
    # Obtener la extensión del archivo
    ext = filename.split('.')[-1]
    # Devolver la ruta de subida del archivo
    return f'img/profile/{identificacion}/{filename}'

class UserType(BaseModel):
    """
    Modelo para manejar los diferentes tipos de usuarios del sistema
    """
    name = models.CharField(
        'Nombre',
        max_length=100,
        unique=True
    )
    code = models.CharField(
        'Código',
        max_length=50,
        unique=True,
        help_text='Código único para identificar el tipo de usuario'
    )
    description = models.TextField(
        'Descripción',
        blank=True
    )
    is_active = models.BooleanField(
        'Activo',
        default=True
    )
    level = models.PositiveIntegerField(
        'Nivel',
        default=0,
        help_text='Nivel de jerarquía del tipo de usuario'
    )
    default_groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='Grupos por Defecto',
        blank=True,
        help_text='Grupos que se asignarán automáticamente a este tipo de usuario'
    )

    class Meta:
        verbose_name = 'Tipo de Usuario'
        verbose_name_plural = 'Tipos de Usuario'
        ordering = ['level', 'name']

    def __str__(self):
        return self.name

class User(AbstractUser):
    # Campos adicionales
    
    identification_type = models.ForeignKey(
        DocType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users',
        verbose_name=_("Tipo de Identificación"))
    identification_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Número de Identificación")
    )
    image = models.ImageField(
        upload_to=Cargar_imagenes_articulos_path,
        blank=True,
        null=True,
        verbose_name=_("Imagen de Perfil")
    )
    def get_image(self):
        if self.image and hasattr(self.image, 'url'):  # Verifica si hay imagen y tiene URL
            return self.image.url
        return static('assets/img/profile/default-user.jpg')
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.identification_number})"

    class Meta:
        verbose_name = _("Usuario")
        verbose_name_plural = _("Usuarios")

class UserProfile(models.Model):
    TYPES = (
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
    )
    # Relación con el usuario de Django
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_("Usuario")
    )

    # Datos personales
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Fecha de Nacimiento")
    )
    gender = models.ForeignKey(
        'Gender',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Género")
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Número de Teléfono")
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Dirección")
    )
    type = models.CharField(max_length=10, choices=TYPES, default='free')
    inscription_date = models.DateTimeField(auto_now_add=True)
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Ciudad")
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("País")
    )
    state = models.ForeignKey(
        State,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Estado")
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Ciudad")
    )
    

    # Configuración de tema
    theme = models.ForeignKey(
        ThemeType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Tema")
    )

    # Configuración de zona horaria
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        verbose_name=_("Zona Horaria")
    )

    # Configuraciones propias de cada usuario
    receive_notifications = models.BooleanField(
        default=True,
        verbose_name=_("Recibir Notificaciones")
    )
    email_notifications = models.BooleanField(
        default=True,
        verbose_name=_("Notificaciones por Correo")
    )
    language = models.CharField(
        max_length=10,
        default='es',
        verbose_name=_("Idioma")
    )

    # Campos adicionales
    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Biografía")
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        verbose_name=_("Foto de Perfil")
    )

    
    
    def get_plan_display(self):
        """Get the display name of the current plan"""
        plan_map = {
            'free': 'Gratuito',
            'basic': 'Básico',
            'premium': 'Premium'
        }
        return plan_map.get(self.plan_actual, 'Gratuito')
    
    def is_premium_user(self):
        """Check if user has premium plan"""
        return self.plan_actual == 'premium'
    
    def is_basic_user(self):
        """Check if user has basic plan"""
        return self.plan_actual == 'basic'
    
    def is_paid_user(self):
        """Check if user has any paid plan"""
        return self.plan_actual in ['basic', 'premium']
    

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.identification_number})"

    class Meta:
        verbose_name = _("Perfil de Usuario")
        verbose_name_plural = _("Perfiles de Usuario")