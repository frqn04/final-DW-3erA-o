from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models


class UserManager(BaseUserManager):
    """
    Manager personalizado para el modelo User.
    """
    def create_user(self, email, dni, password=None, **extra_fields):
        """
        Crea y guarda un usuario con el email, DNI y contraseña dados.
        """
        if not email:
            raise ValueError('El email es obligatorio')
        if not dni:
            raise ValueError('El DNI es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(email=email, dni=dni, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, dni, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con el email, DNI y contraseña dados.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        extra_fields.setdefault('must_change_password', False)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, dni, password, **extra_fields)


class User(AbstractUser):
    """
    Usuario personalizado que hereda de AbstractUser.
    Soporta autenticación con email o DNI.
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('ALUMNO', 'Alumno'),
        ('INVITADO', 'Invitado'),
    ]
    
    # Campos adicionales
    email = models.EmailField('Correo Electrónico', unique=True)
    dni = models.CharField(
        'DNI',
        max_length=8,
        unique=True,
        validators=[
            RegexValidator(r'^\d{8}$', 'El DNI debe contener exactamente 8 dígitos numéricos')
        ]
    )
    role = models.CharField(
        'Rol',
        max_length=10,
        choices=ROLE_CHOICES,
        default='INVITADO'
    )
    phone = models.CharField('Teléfono', max_length=20, blank=True)
    address = models.TextField('Dirección', blank=True)
    
    # Control de cambio de contraseña
    must_change_password = models.BooleanField(
        'Debe cambiar contraseña',
        default=True,
        help_text='Indica si el usuario debe cambiar su contraseña en el próximo login'
    )
    password_changed_at = models.DateTimeField(
        'Contraseña cambiada en',
        null=True,
        blank=True
    )
    
    # Redefinir username como no obligatorio (usaremos email o DNI)
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True
    )
    
    # Manager personalizado
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['dni', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def save(self, *args, **kwargs):
        # Si no tiene username, usar el email
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
    
    # Métodos de utilidad para verificar roles
    def is_admin(self):
        """Verifica si el usuario es administrador"""
        return self.role == 'ADMIN'
    
    def is_alumno(self):
        """Verifica si el usuario es alumno"""
        return self.role == 'ALUMNO'
    
    def is_invitado(self):
        """Verifica si el usuario es invitado"""
        return self.role == 'INVITADO'
    
    def get_role_display_name(self):
        """Obtiene el nombre del rol en español"""
        return dict(self.ROLE_CHOICES).get(self.role, 'Desconocido')
