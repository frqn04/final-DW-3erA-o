"""
Modelos para la gestión de usuarios del sistema escolar.

Este módulo contiene el modelo User personalizado que maneja diferentes tipos de usuarios
en el sistema: administradores, alumnos e invitados.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class User(AbstractUser):
    """
    Modelo de Usuario personalizado para el sistema escolar.
    
    Características principales:
    - Usa email como campo de autenticación principal en lugar de username
    - Incluye DNI único para identificación oficial
    - Maneja diferentes roles de usuario (Admin, Alumno, Invitado)
    - Sistema de cambio forzado de contraseña para nuevos usuarios
    - Campos adicionales para gestión escolar
    """
    
    class UserRole(models.TextChoices):
        """Opciones de roles disponibles para los usuarios del sistema."""
        ADMIN = 'ADMIN', 'Administrador'
        ALUMNO = 'ALUMNO', 'Alumno'
        PROFESOR = 'PROFESOR', 'Profesor'
        PADRE = 'PADRE', 'Padre/Tutor'
        INVITADO = 'INVITADO', 'Invitado'
    
    class UserStatus(models.TextChoices):
        """Estados del usuario en el sistema."""
        ACTIVE = 'ACTIVE', 'Activo'
        INACTIVE = 'INACTIVE', 'Inactivo'
        SUSPENDED = 'SUSPENDED', 'Suspendido'
        PENDING = 'PENDING', 'Pendiente de Aprobación'
    
    # Campos personalizados principales
    username = None  # Eliminamos username, usaremos email como identificador principal
    
    # ID único para referencia externa (útil para APIs)
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='UUID',
        help_text='Identificador único universal del usuario'
    )
    
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
    
    # Campos de rol y estado
    role = models.CharField(
        max_length=15,
        choices=UserRole.choices,
        default=UserRole.INVITADO,
        verbose_name='Rol del usuario',
        help_text='Tipo de usuario en el sistema escolar'
    )
    
    status = models.CharField(
        max_length=15,
        choices=UserStatus.choices,
        default=UserStatus.PENDING,
        verbose_name='Estado del usuario',
        help_text='Estado actual del usuario en el sistema'
    )
    
    # Campos de seguridad
    must_change_password = models.BooleanField(
        default=True,
        verbose_name='Debe cambiar contraseña',
        help_text='Indica si el usuario debe cambiar su contraseña en el próximo inicio de sesión'
    )
    
    password_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de cambio de contraseña',
        help_text='Última vez que el usuario cambió su contraseña'
    )
    
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name='Intentos fallidos de login',
        help_text='Número de intentos de login fallidos consecutivos'
    )
    
    last_failed_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último intento fallido',
        help_text='Fecha y hora del último intento de login fallido'
    )
    
    # Campos adicionales de información personal
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono',
        help_text='Número de teléfono del usuario'
    )
    
    address = models.TextField(
        blank=True,
        verbose_name='Dirección',
        help_text='Dirección física del usuario'
    )
    
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de nacimiento',
        help_text='Fecha de nacimiento del usuario'
    )
    
    # Campos de auditoría adicionales
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        verbose_name='Creado por',
        help_text='Usuario que creó esta cuenta'
    )
    
    last_password_reset = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último reset de contraseña',
        help_text='Fecha del último reset de contraseña'
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
            models.Index(fields=['status']),
            models.Index(fields=['uuid']),
            models.Index(fields=['created_by']),
            models.Index(fields=['last_login']),
        ]
        permissions = [
            ('can_manage_users', 'Puede gestionar usuarios'),
            ('can_reset_passwords', 'Puede resetear contraseñas'),
            ('can_change_user_roles', 'Puede cambiar roles de usuarios'),
            ('can_view_user_reports', 'Puede ver reportes de usuarios'),
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
    
    def is_profesor(self):
        """
        Verifica si el usuario tiene rol de profesor.
        
        Returns:
            bool: True si es profesor, False en caso contrario
        """
        return self.role == self.UserRole.PROFESOR
    
    def is_padre(self):
        """
        Verifica si el usuario tiene rol de padre/tutor.
        
        Returns:
            bool: True si es padre/tutor, False en caso contrario
        """
        return self.role == self.UserRole.PADRE
    
    def is_invitado(self):
        """
        Verifica si el usuario tiene rol de invitado.
        
        Returns:
            bool: True si es invitado, False en caso contrario
        """
        return self.role == self.UserRole.INVITADO
    
    # Métodos de utilidad para verificar estado
    def is_user_active(self):
        """
        Verifica si el usuario está activo en el sistema.
        
        Returns:
            bool: True si está activo, False en caso contrario
        """
        return self.status == self.UserStatus.ACTIVE and self.is_active
    
    def is_suspended(self):
        """
        Verifica si el usuario está suspendido.
        
        Returns:
            bool: True si está suspendido, False en caso contrario
        """
        return self.status == self.UserStatus.SUSPENDED
    
    def is_pending_approval(self):
        """
        Verifica si el usuario está pendiente de aprobación.
        
        Returns:
            bool: True si está pendiente, False en caso contrario
        """
        return self.status == self.UserStatus.PENDING
    
    def get_role_display_icon(self):
        """
        Devuelve un icono representativo del rol del usuario.
        
        Returns:
            str: Icono HTML/CSS class para el rol
        """
        icons = {
            self.UserRole.ADMIN: 'fas fa-user-shield',
            self.UserRole.ALUMNO: 'fas fa-user-graduate',
            self.UserRole.PROFESOR: 'fas fa-chalkboard-teacher',
            self.UserRole.PADRE: 'fas fa-users',
            self.UserRole.INVITADO: 'fas fa-user',
        }
        return icons.get(self.role, 'fas fa-user')
    
    def get_status_display_icon(self):
        """
        Devuelve un icono representativo del estado del usuario.
        
        Returns:
            str: Icono HTML/CSS class para el estado
        """
        icons = {
            self.UserStatus.ACTIVE: 'fas fa-check-circle text-success',
            self.UserStatus.INACTIVE: 'fas fa-times-circle text-secondary',
            self.UserStatus.SUSPENDED: 'fas fa-ban text-danger',
            self.UserStatus.PENDING: 'fas fa-clock text-warning',
        }
        return icons.get(self.status, 'fas fa-question-circle')
    
    def get_age(self):
        """
        Calcula la edad del usuario basada en su fecha de nacimiento.
        
        Returns:
            int: Edad en años o None si no hay fecha de nacimiento
        """
        if not self.birth_date:
            return None
        
        today = timezone.now().date()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    # Métodos de seguridad
    def increment_failed_login(self):
        """
        Incrementa el contador de intentos fallidos de login.
        """
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        self.save(update_fields=['failed_login_attempts', 'last_failed_login'])
    
    def reset_failed_login_attempts(self):
        """
        Resetea el contador de intentos fallidos de login.
        """
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.save(update_fields=['failed_login_attempts', 'last_failed_login'])
    
    def is_account_locked(self):
        """
        Verifica si la cuenta está bloqueada por intentos fallidos.
        
        Returns:
            bool: True si está bloqueada, False en caso contrario
        """
        max_attempts = 5  # Configurable
        lockout_duration = 30  # minutos
        
        if self.failed_login_attempts >= max_attempts:
            if self.last_failed_login:
                time_since_last_fail = timezone.now() - self.last_failed_login
                return time_since_last_fail.total_seconds() < (lockout_duration * 60)
        return False
    
    def set_password(self, raw_password):
        """
        Sobrescribe set_password para trackear cambios de contraseña.
        
        Args:
            raw_password: La nueva contraseña en texto plano
        """
        super().set_password(raw_password)
        self.password_changed_at = timezone.now()
        self.must_change_password = False
    
    def activate_user(self):
        """
        Activa el usuario y lo marca como aprobado.
        """
        self.status = self.UserStatus.ACTIVE
        self.is_active = True
        self.save(update_fields=['status', 'is_active'])
    
    def suspend_user(self, reason=None):
        """
        Suspende al usuario.
        
        Args:
            reason: Motivo de la suspensión (opcional)
        """
        self.status = self.UserStatus.SUSPENDED
        self.is_active = False
        self.save(update_fields=['status', 'is_active'])
        
        # Aquí se podría agregar un log del motivo de suspensión
        if reason:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Usuario {self.email} suspendido. Motivo: {reason}")
    
    def can_login(self):
        """
        Verifica si el usuario puede hacer login.
        
        Returns:
            bool: True si puede hacer login, False en caso contrario
        """
        return (
            self.is_active and 
            self.is_user_active() and 
            not self.is_account_locked() and
            not self.is_suspended()
        )
    
    
    def clean(self):
        """
        Validaciones adicionales del modelo.
        
        Raises:
            ValidationError: Si hay errores de validación
        """
        from django.core.exceptions import ValidationError
        import re
        
        super().clean()
        
        errors = {}
        
        # Validar que el email esté presente
        if not self.email:
            errors['email'] = 'El correo electrónico es obligatorio.'
        else:
            # Normalizar email a minúsculas
            self.email = self.email.lower().strip()
            
            # Validación de formato de email más estricta
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.email):
                errors['email'] = 'Formato de correo electrónico inválido.'
        
        # Validar DNI
        if not self.dni:
            errors['dni'] = 'El DNI es obligatorio.'
        else:
            # Limpiar espacios del DNI
            self.dni = self.dni.strip()
            
            # Validar formato básico del DNI (solo números y letras, sin espacios)
            if not re.match(r'^[a-zA-Z0-9]+$', self.dni):
                errors['dni'] = 'El DNI debe contener solo números y letras, sin espacios.'
            
            # Validar longitud mínima del DNI
            if len(self.dni) < 5:
                errors['dni'] = 'El DNI debe tener al menos 5 caracteres.'
        
        # Validar nombres si están presentes
        if self.first_name:
            self.first_name = self.first_name.strip().title()
            if len(self.first_name) < 2:
                errors['first_name'] = 'El nombre debe tener al menos 2 caracteres.'
        
        if self.last_name:
            self.last_name = self.last_name.strip().title()
            if len(self.last_name) < 2:
                errors['last_name'] = 'El apellido debe tener al menos 2 caracteres.'
        
        # Validar teléfono si está presente
        if self.phone:
            phone_clean = re.sub(r'[^\d+\-\s\(\)]', '', self.phone)
            if len(phone_clean) < 7:
                errors['phone'] = 'El número de teléfono debe tener al menos 7 dígitos.'
            self.phone = phone_clean
        
        # Validar fecha de nacimiento
        if self.birth_date:
            from django.utils import timezone
            today = timezone.now().date()
            
            if self.birth_date > today:
                errors['birth_date'] = 'La fecha de nacimiento no puede ser futura.'
            
            # Validar edad mínima (3 años) y máxima (120 años)
            age = today.year - self.birth_date.year
            if age < 3:
                errors['birth_date'] = 'La edad mínima es 3 años.'
            elif age > 120:
                errors['birth_date'] = 'La edad máxima es 120 años.'
        
        # Validar coherencia de roles y estados
        if self.role == self.UserRole.ADMIN and not self.is_staff:
            self.is_staff = True  # Los admins deben ser staff
        
        if errors:
            raise ValidationError(errors)
    
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


# Manager personalizado para el modelo User
class UserManager(models.Manager):
    """
    Manager personalizado para el modelo User con métodos de conveniencia.
    """
    
    def active_users(self):
        """Devuelve solo usuarios activos."""
        return self.filter(status=User.UserStatus.ACTIVE, is_active=True)
    
    def by_role(self, role):
        """Filtra usuarios por rol."""
        return self.filter(role=role)
    
    def admins(self):
        """Devuelve solo administradores."""
        return self.by_role(User.UserRole.ADMIN)
    
    def alumnos(self):
        """Devuelve solo alumnos."""
        return self.by_role(User.UserRole.ALUMNO)
    
    def profesores(self):
        """Devuelve solo profesores."""
        return self.by_role(User.UserRole.PROFESOR)
    
    def padres(self):
        """Devuelve solo padres/tutores."""
        return self.by_role(User.UserRole.PADRE)
    
    def pending_approval(self):
        """Devuelve usuarios pendientes de aprobación."""
        return self.filter(status=User.UserStatus.PENDING)
    
    def suspended_users(self):
        """Devuelve usuarios suspendidos."""
        return self.filter(status=User.UserStatus.SUSPENDED)


# Agregar el manager personalizado al modelo User
User.add_to_class('objects', UserManager())


# Signals para el modelo User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, **kwargs):
    """
    Signal que se ejecuta antes de guardar un usuario.
    
    Args:
        sender: La clase del modelo que envió la señal
        instance: La instancia del usuario que se va a guardar
        **kwargs: Argumentos adicionales
    """
    # Si es un usuario existente y se cambió la contraseña
    if instance.pk:
        try:
            old_user = User.objects.get(pk=instance.pk)
            if old_user.password != instance.password:
                instance.password_changed_at = timezone.now()
                instance.must_change_password = False
                instance.reset_failed_login_attempts()
        except User.DoesNotExist:
            pass


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
        logger.info(f"Nuevo usuario creado: {instance.email} - Rol: {instance.role}")
        
        # Configuraciones automáticas para nuevos usuarios
        if instance.role == User.UserRole.ADMIN:
            instance.is_staff = True
            instance.status = User.UserStatus.ACTIVE
            instance.save(update_fields=['is_staff', 'status'])
        
        # Aquí se pueden agregar más lógicas como:
        # - Envío de email de bienvenida
        # - Creación de perfil relacionado
        # - Asignación de permisos por defecto
        # - Notificaciones a administradores
    else:
        # Usuario actualizado
        logger.info(f"Usuario actualizado: {instance.email}")


# Modelo adicional para tracking de actividad de usuarios
class UserActivityLog(models.Model):
    """
    Modelo para registrar actividades importantes de los usuarios.
    """
    
    class ActivityType(models.TextChoices):
        LOGIN = 'LOGIN', 'Inicio de sesión'
        LOGOUT = 'LOGOUT', 'Cierre de sesión'
        PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'Cambio de contraseña'
        FAILED_LOGIN = 'FAILED_LOGIN', 'Intento de login fallido'
        ACCOUNT_LOCKED = 'ACCOUNT_LOCKED', 'Cuenta bloqueada'
        PROFILE_UPDATE = 'PROFILE_UPDATE', 'Actualización de perfil'
        ROLE_CHANGE = 'ROLE_CHANGE', 'Cambio de rol'
        STATUS_CHANGE = 'STATUS_CHANGE', 'Cambio de estado'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name='Usuario'
    )
    
    activity_type = models.CharField(
        max_length=20,
        choices=ActivityType.choices,
        verbose_name='Tipo de actividad'
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y hora'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Detalles adicionales'
    )
    
    class Meta:
        verbose_name = 'Log de Actividad de Usuario'
        verbose_name_plural = 'Logs de Actividad de Usuarios'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['activity_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()} - {self.timestamp}"
