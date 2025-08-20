"""
Modelos para la app students.

Este módulo contiene los modelos relacionados con estudiantes y personas del sistema educativo.

Arquitectura de Modelos:
========================

1. Persona (Modelo Abstracto):
   - Proporciona campos comunes para cualquier tipo de persona del sistema
   - No crea tabla en la base de datos (abstract=True)
   - Permite reutilización de código y consistencia de datos
   - Facilita futuras extensiones (Profesor, Administrativo, etc.)

2. Alumno (Modelo Concreto):
   - Hereda de Persona todos los campos básicos
   - Añade campos específicos de estudiantes
   - Se relaciona con Carrera mediante FK con PROTECT
   - Crea su propia tabla incluyendo campos heredados

Razones para usar Modelo Abstracto:
===================================

✅ REUTILIZACIÓN DE CÓDIGO:
   - Evita duplicar campos como first_name, last_name, dni, email
   - Centraliza validaciones comunes en un solo lugar
   - Facilita el mantenimiento del código

✅ ESCALABILIDAD:
   - Permite crear fácilmente otros tipos de personas (Profesor, Administrativo)
   - Mantiene consistencia en la estructura de datos
   - Facilita migraciones futuras

✅ FLEXIBILIDAD:
   - Cada modelo concreto puede tener su propia tabla optimizada
   - No hay JOIN innecesarios como en herencia multi-tabla
   - Mejor rendimiento en consultas

✅ VALIDACIONES CENTRALIZADAS:
   - Las validaciones de DNI, email se aplican automáticamente
   - Métodos comunes como __str__, clean() se heredan
   - Propiedades calculadas disponibles en todos los modelos hijos

Relaciones Implementadas:
=========================
- Alumno -> Carrera (FK, PROTECT): Si se intenta eliminar una carrera con alumnos, 
  Django impedirá la eliminación para proteger la integridad referencial.
"""

from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
import re


class Persona(models.Model):
    """
    Modelo abstracto que define los campos comunes para cualquier persona del sistema.
    
    Este modelo no crea una tabla en la base de datos (abstract=True), 
    sino que sirve como plantilla para otros modelos que representen personas.
    
    Campos Incluidos:
    ================
    - first_name: Nombre(s) de la persona
    - last_name: Apellido(s) de la persona  
    - dni: Documento Nacional de Identidad (único)
    - email: Correo electrónico (único)
    - fecha_creacion: Timestamp de creación automático
    - fecha_actualizacion: Timestamp de actualización automático
    
    Validaciones Implementadas:
    ===========================
    - DNI: Solo números, entre 7 y 8 dígitos
    - Email: Formato válido y único en el sistema
    - Nombres: Sin números ni caracteres especiales
    - Campos requeridos: first_name, last_name, dni, email
    """
    
    # Validador para DNI argentino (7-8 dígitos)
    dni_validator = RegexValidator(
        regex=r'^\d{7,8}$',
        message='El DNI debe contener entre 7 y 8 dígitos numéricos.'
    )
    
    # Validador para nombres (solo letras, espacios, acentos)
    name_validator = RegexValidator(
        regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
        message='El nombre solo puede contener letras, espacios y acentos.'
    )
    
    first_name = models.CharField(
        'Nombre(s)',
        max_length=50,
        validators=[name_validator],
        help_text='Nombre(s) de la persona. Solo letras y espacios.'
    )
    
    last_name = models.CharField(
        'Apellido(s)', 
        max_length=50,
        validators=[name_validator],
        help_text='Apellido(s) de la persona. Solo letras y espacios.'
    )
    
    dni = models.CharField(
        'DNI',
        max_length=8,
        unique=True,
        validators=[dni_validator],
        help_text='Documento Nacional de Identidad. Entre 7 y 8 dígitos.',
        error_messages={
            'unique': 'Ya existe una persona con este DNI en el sistema.'
        }
    )
    
    email = models.EmailField(
        'Correo Electrónico',
        unique=True,
        validators=[EmailValidator()],
        help_text='Dirección de correo electrónico válida.',
        error_messages={
            'unique': 'Ya existe una persona con este email en el sistema.'
        }
    )
    
    # Campos de auditoría automáticos
    fecha_creacion = models.DateTimeField(
        'Fecha de Creación',
        auto_now_add=True,
        help_text='Fecha y hora de creación del registro.'
    )
    
    fecha_actualizacion = models.DateTimeField(
        'Fecha de Actualización',
        auto_now=True,
        help_text='Fecha y hora de la última actualización.'
    )
    
    class Meta:
        abstract = True  # ¡IMPORTANTE! Esto hace que sea un modelo abstracto
        ordering = ['last_name', 'first_name']
        
    def clean(self):
        """
        Validaciones personalizadas a nivel de modelo.
        
        Se ejecuta antes de save() y valida:
        - Formato del DNI
        - Formato del email
        - Longitud mínima de nombres
        """
        super().clean()
        
        # Validar longitud mínima de nombres
        if len(self.first_name.strip()) < 2:
            raise ValidationError({
                'first_name': 'El nombre debe tener al menos 2 caracteres.'
            })
            
        if len(self.last_name.strip()) < 2:
            raise ValidationError({
                'last_name': 'El apellido debe tener al menos 2 caracteres.'
            })
        
        # Validar que el DNI no comience con 0 (opcional, según normativa)
        if self.dni.startswith('0'):
            raise ValidationError({
                'dni': 'El DNI no puede comenzar con 0.'
            })
            
        # Normalizar email a minúsculas
        if self.email:
            self.email = self.email.lower().strip()
    
    def save(self, *args, **kwargs):
        """
        Método save personalizado que ejecuta validaciones antes de guardar.
        """
        # Normalizar datos antes de guardar
        self.first_name = self.first_name.strip().title()
        self.last_name = self.last_name.strip().title()
        self.dni = self.dni.strip()
        
        # Ejecutar validaciones
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        """
        Representación en string del modelo.
        Formato: "Apellido, Nombre (DNI: 12345678)"
        """
        return f"{self.last_name}, {self.first_name} (DNI: {self.dni})"
    
    @property
    def nombre_completo(self):
        """
        Propiedad que devuelve el nombre completo.
        Formato: "Nombre Apellido"
        """
        return f"{self.first_name} {self.last_name}"
    
    @property
    def apellido_nombre(self):
        """
        Propiedad que devuelve apellido y nombre.
        Formato: "Apellido, Nombre"
        """
        return f"{self.last_name}, {self.first_name}"
    
    @property
    def iniciales(self):
        """
        Propiedad que devuelve las iniciales.
        Formato: "N.A." (primera letra del nombre y apellido)
        """
        return f"{self.first_name[0].upper()}.{self.last_name[0].upper()}."


class Alumno(Persona):
    """
    Modelo que representa a un estudiante del sistema educativo.
    
    Hereda de Persona todos los campos básicos (first_name, last_name, dni, email)
    y añade campos específicos para la gestión académica de estudiantes.
    
    Relaciones:
    ===========
    - carrera (FK a Carrera, PROTECT): Carrera en la que está inscripto el alumno.
      Usa PROTECT para evitar eliminar carreras con alumnos inscriptos.
    
    Campos Adicionales:
    ===================
    - legajo: Número único de identificación académica
    - fecha_ingreso: Fecha de ingreso a la institución
    - activo: Estado del alumno (activo/inactivo)
    - observaciones: Notas adicionales sobre el alumno
    
    Estados del Alumno:
    ===================
    - ACTIVO: Alumno cursando normalmente
    - INACTIVO: Alumno que no está cursando (licencia, abandono temporal)
    """
    
    # Importación local para evitar dependencias circulares
    from escuelas.models import Carrera
    
    legajo = models.CharField(
        'Legajo',
        max_length=20,
        unique=True,
        help_text='Número único de identificación académica del alumno.',
        error_messages={
            'unique': 'Ya existe un alumno con este legajo.'
        }
    )
    
    carrera = models.ForeignKey(
        'escuelas.Carrera',  # Referencia por string para evitar importación circular
        on_delete=models.PROTECT,  # PROTECT: No permite eliminar carrera con alumnos
        verbose_name='Carrera',
        related_name='alumnos',
        null=True,
        blank=True,
        help_text='Carrera en la que está inscripto el alumno. Se protege contra eliminación.'
    )
    
    fecha_ingreso = models.DateField(
        'Fecha de Ingreso',
        default=timezone.now,
        help_text='Fecha de ingreso del alumno a la institución.'
    )
    
    activo = models.BooleanField(
        'Activo',
        default=True,
        help_text='Indica si el alumno está actualmente cursando.'
    )
    
    observaciones = models.TextField(
        'Observaciones',
        blank=True,
        max_length=500,
        help_text='Notas adicionales sobre el alumno (máximo 500 caracteres).'
    )
    
    class Meta:
        verbose_name = 'Alumno'
        verbose_name_plural = 'Alumnos'
        ordering = ['carrera__nombre', 'last_name', 'first_name']
        
        # Índices para mejorar el rendimiento
        indexes = [
            models.Index(fields=['legajo']),
            models.Index(fields=['carrera', 'activo']),
            models.Index(fields=['fecha_ingreso']),
            models.Index(fields=['dni']),  # Heredado de Persona pero útil indexar
        ]
        
        # Restricciones a nivel de base de datos
        constraints = [
            models.CheckConstraint(
                check=models.Q(fecha_ingreso__lte=timezone.now().date()),
                name='fecha_ingreso_no_futura'
            ),
        ]
    
    def clean(self):
        """
        Validaciones personalizadas para el modelo Alumno.
        """
        super().clean()  # Ejecuta validaciones de Persona
        
        # Validar que la fecha de ingreso no sea futura
        if self.fecha_ingreso and self.fecha_ingreso > timezone.now().date():
            raise ValidationError({
                'fecha_ingreso': 'La fecha de ingreso no puede ser futura.'
            })
        
        # Validar legajo (debe ser alfanumérico)
        if self.legajo and not re.match(r'^[A-Za-z0-9]+$', self.legajo):
            raise ValidationError({
                'legajo': 'El legajo solo puede contener letras y números.'
            })
    
    def save(self, *args, **kwargs):
        """
        Método save personalizado para Alumno.
        """
        # Generar legajo automáticamente si no existe
        if not self.legajo:
            self.legajo = self.generar_legajo()
        
        # Normalizar legajo
        self.legajo = self.legajo.upper().strip()
        
        super().save(*args, **kwargs)
    
    def generar_legajo(self):
        """
        Genera un legajo único para el alumno.
        Formato: {año_ingreso}{carrera_codigo}{numero_secuencial}
        Ejemplo: 2024ING001, 2024ADM002
        """
        año = self.fecha_ingreso.year if self.fecha_ingreso else timezone.now().year
        
        if self.carrera and self.carrera.codigo:
            prefijo = f"{año}{self.carrera.codigo[:3].upper()}"
        else:
            prefijo = f"{año}GEN"  # General si no tiene carrera
        
        # Buscar el último número secuencial
        ultimo_alumno = Alumno.objects.filter(
            legajo__startswith=prefijo
        ).order_by('legajo').last()
        
        if ultimo_alumno:
            try:
                ultimo_numero = int(ultimo_alumno.legajo[len(prefijo):])
                nuevo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                nuevo_numero = 1
        else:
            nuevo_numero = 1
        
        return f"{prefijo}{nuevo_numero:03d}"  # Formato con 3 dígitos: 001, 002, etc.
    
    def get_absolute_url(self):
        """
        URL absoluta para ver el detalle del alumno.
        """
        return reverse('students:alumno_detail', kwargs={'pk': self.pk})
    
    @property
    def años_en_institucion(self):
        """
        Calcula los años que lleva el alumno en la institución.
        """
        if self.fecha_ingreso:
            today = timezone.now().date()
            return today.year - self.fecha_ingreso.year
        return 0
    
    @property
    def estado_display(self):
        """
        Devuelve el estado del alumno en formato legible.
        """
        return "Activo" if self.activo else "Inactivo"
    
    @property
    def carrera_nombre(self):
        """
        Devuelve el nombre de la carrera o "Sin carrera" si no tiene.
        """
        return self.carrera.nombre if self.carrera else "Sin carrera asignada"
    
    def __str__(self):
        """
        Representación en string del Alumno.
        Formato: "Apellido, Nombre (Legajo: ABC123) - Carrera"
        """
        carrera_info = f" - {self.carrera.nombre}" if self.carrera else ""
        return f"{self.apellido_nombre} (Legajo: {self.legajo}){carrera_info}"


# ==========================================
# SIGNALS PARA AUDITORÍA Y LOGGING
# ==========================================

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Alumno)
def alumno_pre_save(sender, instance, **kwargs):
    """
    Signal que se ejecuta antes de guardar un Alumno.
    Útil para logging y validaciones adicionales.
    """
    if instance.pk:  # Es una actualización
        try:
            old_instance = Alumno.objects.get(pk=instance.pk)
            if old_instance.carrera != instance.carrera:
                logger.info(
                    f"Alumno {instance.legajo} cambió de carrera: "
                    f"{old_instance.carrera} -> {instance.carrera}"
                )
        except Alumno.DoesNotExist:
            pass


@receiver(post_save, sender=Alumno)
def alumno_post_save(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar un Alumno.
    """
    if created:
        logger.info(f"Nuevo alumno creado: {instance.legajo} - {instance.nombre_completo}")
    else:
        logger.info(f"Alumno actualizado: {instance.legajo} - {instance.nombre_completo}")
