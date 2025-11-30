from django.conf import settings
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils import timezone


class Persona(models.Model):
    """
    Clase abstracta que representa a una persona.
    Implementa principios de POO (herencia).
    """
    first_name = models.CharField('Nombre', max_length=100)
    last_name = models.CharField('Apellido', max_length=100)
    dni = models.CharField(
        'DNI',
        max_length=8,
        unique=True,
        validators=[
            RegexValidator(r'^\d{8}$', 'El DNI debe contener exactamente 8 dígitos numéricos')
        ]
    )
    email = models.EmailField('Email', unique=True)
    
    class Meta:
        abstract = True
    
    def __str__(self):
        return f"{self.last_name}, {self.first_name}"
    
    def get_full_name(self):
        """Retorna el nombre completo de la persona"""
        return f"{self.first_name} {self.last_name}"


class Alumno(Persona):
    """
    Modelo que representa a un alumno.
    Hereda de Persona (POO).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='alumno',
        verbose_name='Usuario',
        null=True,
        blank=True,
        help_text='Usuario asociado al alumno (opcional)'
    )
    legajo = models.CharField(
        'Legajo',
        max_length=20,
        unique=True,
        help_text='Formato: {año}{codigo_carrera}{nro_secuencial}'
    )
    carrera = models.ForeignKey(
        'escuelas.Carrera',
        on_delete=models.PROTECT,
        related_name='alumnos',
        verbose_name='Carrera'
    )
    fecha_ingreso = models.DateField('Fecha de ingreso', default=timezone.now)
    activo = models.BooleanField('Activo', default=True)
    observaciones = models.TextField('Observaciones', blank=True)
    
    class Meta:
        verbose_name = 'Alumno'
        verbose_name_plural = 'Alumnos'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.legajo} - {self.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """
        Genera el legajo automáticamente si no existe.
        Formato: {año}{codigo_carrera}{nro_secuencial}
        """
        if not self.legajo:
            año = timezone.now().year
            codigo_carrera = self.carrera.codigo
            
            # Obtener el último número secuencial para este año y carrera
            ultimo_alumno = Alumno.objects.filter(
                legajo__startswith=f"{año}{codigo_carrera}"
            ).order_by('-legajo').first()
            
            if ultimo_alumno:
                # Extraer el número secuencial del último legajo
                try:
                    ultimo_nro = int(ultimo_alumno.legajo[len(f"{año}{codigo_carrera}"):])
                    nuevo_nro = ultimo_nro + 1
                except (ValueError, IndexError):
                    nuevo_nro = 1
            else:
                nuevo_nro = 1
            
            # Generar el nuevo legajo con formato: año + código_carrera + número (3 dígitos)
            self.legajo = f"{año}{codigo_carrera}{nuevo_nro:03d}"
        
        super().save(*args, **kwargs)
    
    def materias_cursando(self):
        """Retorna las materias que el alumno está cursando actualmente"""
        from enrollments.models import Inscripcion
        return Inscripcion.objects.filter(
            alumno=self,
            estado='CURSANDO'
        ).select_related('materia')
    
    def materias_aprobadas(self):
        """Retorna las materias que el alumno ha aprobado"""
        from enrollments.models import Inscripcion
        return Inscripcion.objects.filter(
            alumno=self,
            estado='APROBADO'
        ).select_related('materia')
