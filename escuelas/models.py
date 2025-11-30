from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
import random
import string


class Carrera(models.Model):
    """
    Modelo que representa una carrera universitaria.
    """
    codigo = models.CharField(
        'Código',
        max_length=10,
        unique=True,
        help_text='Código único de la carrera (ej: ING, LIC, TEC)'
    )
    nombre = models.CharField(
        'Nombre',
        max_length=200,
        unique=True
    )
    duracion_años = models.PositiveIntegerField(
        'Duración en años',
        validators=[MinValueValidator(1)]
    )
    descripcion = models.TextField('Descripción', blank=True)
    activa = models.BooleanField('Activa', default=True)
    
    class Meta:
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def delete(self, *args, **kwargs):
        """
        Prevenir eliminación si tiene materias o alumnos asociados.
        """
        if self.materias.exists():
            raise ValidationError(
                f'⛔ No se puede eliminar la carrera "{self.nombre}" porque tiene {self.materias.count()} materia(s) asociada(s). '
                f'Primero debes eliminar o reasignar las materias.'
            )
        if self.alumnos.exists():
            raise ValidationError(
                f'⛔ No se puede eliminar la carrera "{self.nombre}" porque tiene {self.alumnos.count()} alumno(s) inscripto(s). '
                f'Primero debes reasignar los alumnos a otra carrera.'
            )
        super().delete(*args, **kwargs)


class Materia(models.Model):
    """
    Modelo que representa una materia de una carrera.
    """
    carrera = models.ForeignKey(
        Carrera,
        on_delete=models.PROTECT,
        related_name='materias',
        verbose_name='Carrera'
    )
    nombre = models.CharField('Nombre', max_length=200)
    codigo = models.CharField('Código', max_length=20)
    año_carrera = models.PositiveIntegerField(
        'Año de la carrera',
        validators=[MinValueValidator(1)],
        help_text='Año de la carrera en el que se cursa esta materia'
    )
    cupo_maximo = models.PositiveIntegerField(
        'Cupo máximo',
        validators=[MinValueValidator(1)],
        help_text='Cantidad máxima de alumnos que pueden inscribirse'
    )
    descripcion = models.TextField('Descripción', blank=True)
    activa = models.BooleanField('Activa', default=True)
    
    class Meta:
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'
        ordering = ['carrera', 'año_carrera', 'nombre']
        unique_together = [['carrera', 'codigo'], ['carrera', 'nombre']]
    
    def __str__(self):
        return f"{self.carrera.codigo} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        """
        Genera código aleatorio si no existe.
        Formato: 3 letras + 4 números (ej: ABC1234)
        """
        if not self.codigo:
            while True:
                # Generar código aleatorio: 3 letras + 4 números
                letras = ''.join(random.choices(string.ascii_uppercase, k=3))
                numeros = ''.join(random.choices(string.digits, k=4))
                nuevo_codigo = f"{letras}{numeros}"
                
                # Verificar que no exista para esta carrera
                if not Materia.objects.filter(carrera=self.carrera, codigo=nuevo_codigo).exists():
                    self.codigo = nuevo_codigo
                    break
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Prevenir eliminación si tiene inscripciones asociadas.
        """
        if self.inscripciones.exists():
            inscripciones_activas = self.inscripciones.filter(estado__in=['CURSANDO', 'REGULAR']).count()
            raise ValidationError(
                f'⛔ No se puede eliminar la materia "{self.nombre}" porque tiene {self.inscripciones.count()} inscripción(es) asociada(s) '
                f'({inscripciones_activas} activa(s)). Primero debes eliminar las inscripciones.'
            )
        super().delete(*args, **kwargs)
    
    def inscriptos_actuales(self):
        """
        Retorna la cantidad de alumnos inscriptos actualmente.
        """
        return self.inscripciones.filter(
            estado__in=['CURSANDO', 'REGULAR']
        ).count()
    
    def cupo_disponible(self):
        """
        Retorna la cantidad de cupos disponibles.
        """
        return self.cupo_maximo - self.inscriptos_actuales()
    
    def tiene_cupo_disponible(self):
        """
        Verifica si hay cupo disponible.
        """
        return self.cupo_disponible() > 0
