from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Inscripcion(models.Model):
    """
    Modelo que representa la inscripción de un alumno a una materia.
    """
    ESTADO_CHOICES = [
        ('CURSANDO', 'Cursando'),
        ('REGULAR', 'Regular'),
        ('APROBADO', 'Aprobado'),
        ('DESAPROBADO', 'Desaprobado'),
    ]
    
    alumno = models.ForeignKey(
        'students.Alumno',
        on_delete=models.CASCADE,
        related_name='inscripciones',
        verbose_name='Alumno'
    )
    materia = models.ForeignKey(
        'escuelas.Materia',
        on_delete=models.PROTECT,
        related_name='inscripciones',
        verbose_name='Materia'
    )
    fecha_inscripcion = models.DateField(
        'Fecha de inscripción',
        default=timezone.now
    )
    estado = models.CharField(
        'Estado',
        max_length=15,
        choices=ESTADO_CHOICES,
        default='CURSANDO'
    )
    observaciones = models.TextField('Observaciones', blank=True)
    
    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        ordering = ['-fecha_inscripcion']
        unique_together = [['alumno', 'materia']]
    
    def __str__(self):
        return f"{self.alumno.legajo} - {self.materia.nombre} ({self.get_estado_display()})"
    
    def clean(self):
        """
        Validaciones de negocio:
        1. No permitir inscripción duplicada (alumno + materia)
        2. Verificar que haya cupo disponible
        3. Verificar que el alumno esté activo
        4. Verificar que la materia esté activa
        """
        super().clean()
        
        # Si no hay alumno asignado aún (caso de formulario de alumno), saltar validaciones
        if not self.alumno_id:
            return
        
        # Verificar alumno activo
        if not self.alumno.activo:
            raise ValidationError('El alumno no está activo.')
        
        # Verificar materia activa
        if self.materia and not self.materia.activa:
            raise ValidationError('⚠️ La materia no está activa y no acepta inscripciones.')
        
        # Verificar inscripción duplicada (solo si es nueva inscripción)
        if not self.pk:
            existe = Inscripcion.objects.filter(
                alumno=self.alumno,
                materia=self.materia
            ).exists()
            
            if existe:
                raise ValidationError(
                    f'⚠️ El alumno {self.alumno.get_full_name()} ya está inscripto en la materia "{self.materia.nombre}".'
                )
            
            # Verificar cupo disponible (solo para inscripciones nuevas en estado CURSANDO)
            if self.estado == 'CURSANDO':
                if not self.materia.tiene_cupo_disponible():
                    raise ValidationError(
                        f'⚠️ No hay cupo disponible en "{self.materia.nombre}". '
                        f'Cupo máximo: {self.materia.cupo_maximo} | '
                        f'Inscriptos actuales: {self.materia.inscriptos_actuales()}'
                    )
    
    def save(self, *args, **kwargs):
        """
        Ejecutar validaciones antes de guardar.
        """
        self.clean()
        super().save(*args, **kwargs)
