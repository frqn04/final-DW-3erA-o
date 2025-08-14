"""
Modelos para la gestión de usuarios del sistema escolar.

Este módulo contiene el modelo User personalizado que maneja diferentes tipos de usuarios
en el sistema: administradores, alumnos e invitados.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Modelo de Usuario personalizado para el sistema escolar.
    
    Características principales:
    - Usa email como campo de autenticación principal en lugar de username
    - Incluye DNI único para identificación oficial
    - Maneja diferentes roles de usuario (Admin, Alumno, Invitado)
    - Sistema de cambio forzado de contraseña para nuevos usuarios
    """
    
    class UserRole(models.TextChoices):
        """Opciones de roles disponibles para los usuarios del sistema."""
        ADMIN = 'ADMIN', 'Administrador'
        ALUMNO = 'ALUMNO', 'Alumno'
        INVITADO = 'INVITADO', 'Invitado'
    
    # Campos personalizados
    username = None  # Eliminamos username, usaremos email como identificador principal
    
    email = models.EmailField(
        unique=True,
        verbose_name='Correo electrónico',
        help_text='Dirección de correo electrónico única del usuario'
    )
    
    dni = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='DNI/Cédula',
        help_text='Documento Nacional de Identidad o Cédula de Identidad'
    )
    
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.INVITADO,
        verbose_name='Rol del usuario',
        help_text='Tipo de usuario en el sistema escolar'
    )
    
    must_change_password = models.BooleanField(
        default=True,
        verbose_name='Debe cambiar contraseña',
        help_text='Indica si el usuario debe cambiar su contraseña en el próximo inicio de sesión'
    )
    
    # Configuración del modelo
    USERNAME_FIELD = 'email'  # Usamos email como campo de autenticación
    REQUIRED_FIELDS = ['dni', 'first_name', 'last_name']  # Campos requeridos para crear superusuario
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'users_user'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['dni']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        """
        Representación en cadena del usuario.
        
        Returns:
            str: Formato "Apellido, Nombre (email)"
        """
        if self.first_name and self.last_name:
            return f"{self.last_name}, {self.first_name} ({self.email})"
        return self.email
    
    def get_full_name(self):
        """
        Devuelve el nombre completo del usuario.
        
        Returns:
            str: Nombre completo en formato "Nombre Apellido"
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    def get_short_name(self):
        """
        Devuelve el nombre corto del usuario.
        
        Returns:
            str: Primer nombre o email si no hay nombre
        """
        return self.first_name or self.email
    
    # Métodos de utilidad para verificar roles
    def is_admin(self):
        """
        Verifica si el usuario tiene rol de administrador.
        
        Returns:
            bool: True si es administrador, False en caso contrario
        """
        return self.role == self.UserRole.ADMIN
    
    def is_alumno(self):
        """
        Verifica si el usuario tiene rol de alumno.
        
        Returns:
            bool: True si es alumno, False en caso contrario
        """
        return self.role == self.UserRole.ALUMNO
    
    def is_invitado(self):
        """
        Verifica si el usuario tiene rol de invitado.
        
        Returns:
            bool: True si es invitado, False en caso contrario
        """
        return self.role == self.UserRole.INVITADO
    
    def get_role_display_icon(self):
        """
        Devuelve un icono representativo del rol del usuario.
        
        Returns:
            str: Icono HTML/CSS class para el rol
        """
        icons = {
            self.UserRole.ADMIN: 'fas fa-user-shield',
            self.UserRole.ALUMNO: 'fas fa-user-graduate',
            self.UserRole.INVITADO: 'fas fa-user',
        }
        return icons.get(self.role, 'fas fa-user')
    
    def clean(self):
        """
        Validaciones adicionales del modelo.
        
        Raises:
            ValidationError: Si hay errores de validación
        """
        from django.core.exceptions import ValidationError
        
        super().clean()
        
        # Validar que el email esté presente
        if not self.email:
            raise ValidationError({'email': 'El correo electrónico es obligatorio.'})
        
        # Normalizar email a minúsculas
        if self.email:
            self.email = self.email.lower()
        
        # Validar formato básico del DNI (solo números y letras, sin espacios)
        if self.dni and not self.dni.replace(' ', '').isalnum():
            raise ValidationError({'dni': 'El DNI debe contener solo números y letras.'})
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para aplicar validaciones y normalizaciones.
        
        Args:
            *args: Argumentos posicionales
            **kwargs: Argumentos de palabra clave
        """
        # Ejecutar validaciones
        self.full_clean()
        
        # Llamar al método save del padre
        super().save(*args, **kwargs)


# Signals para el modelo User (se pueden añadir más adelante)
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar un usuario.
    
    Args:
        sender: La clase del modelo que envió la señal
        instance: La instancia del usuario que se guardó
        created: Boolean que indica si es una nueva instancia
        **kwargs: Argumentos adicionales
    """
    if created:
        # Lógica a ejecutar cuando se crea un nuevo usuario
        # Por ejemplo, enviar email de bienvenida, crear perfil, etc.
        pass
