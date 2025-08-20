from django.db import models


class Carrera(models.Model):
    """
    Modelo que representa una carrera académica.
    
    Características:
    - Nombre único: No puede haber dos carreras con el mismo nombre en el sistema
    - Código único: Para identificación administrativa
    - Duración: Para validar materias por año
    - Estado: Para carreras activas/inactivas
    """
    
    nombre = models.CharField(
        max_length=200,
        unique=True,  # REQUERIMIENTO: nombre único
        verbose_name='Nombre de la Carrera',
        help_text='Nombre único de la carrera en todo el sistema'
    )
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código de Carrera',
        help_text='Código único identificatorio (ej: ING-SIS, PROF-MAT)'
    )
    
    duracion_anos = models.PositiveIntegerField(
        default=4,
        verbose_name='Duración en Años',
        help_text='Duración nominal de la carrera en años'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Carrera Activa',
        help_text='Indica si la carrera está disponible para nuevas inscripciones'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada de la carrera y perfil profesional'
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['activa']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"
    
    @property
    def total_materias(self):
        """Retorna el número total de materias de la carrera"""
        return self.materias.count()
    
    @property
    def materias_activas(self):
        """Retorna las materias activas de la carrera"""
        return self.materias.filter(activa=True)


class Materia(models.Model):
    """
    Modelo que representa una materia o asignatura.
    
    ¿Por qué PROTECT en la relación con Carrera?
    ============================================
    
    Se usa on_delete=PROTECT porque:
    
    1. INTEGRIDAD DE DATOS: Si elimináramos una carrera que tiene materias,
       perderíamos información académica valiosa.
    
    2. CONSISTENCIA ACADÉMICA: Las materias necesitan saber a qué carrera 
       pertenecen para mantener la estructura del plan de estudios.
    
    3. PREVENCIÓN DE ERRORES: PROTECT evita eliminaciones accidentales que 
       podrían causar inconsistencias en el sistema.
    
    4. PROCESO CONTROLADO: Obliga a los administradores a:
       - Primero eliminar o reubicar las materias
       - Luego eliminar la carrera de forma consciente
    
    Restricción UniqueConstraint: (carrera, nombre)
    ==============================================
    
    Esta restricción garantiza que:
    
    1. NO puede haber dos materias con el mismo nombre en la misma carrera
       Ejemplo: No puede haber dos "Matemática I" en "Ingeniería en Sistemas"
    
    2. SÍ puede haber materias con el mismo nombre en carreras diferentes
       Ejemplo: "Matemática I" puede existir en "Ingeniería" y en "Profesorado"
    
    3. BENEFICIOS:
       - Evita duplicaciones accidentales en el plan de estudios
       - Permite reutilizar nombres comunes entre carreras
       - Facilita la organización académica
    """
    
    # REQUERIMIENTO: FK a Carrera con on_delete=PROTECT
    carrera = models.ForeignKey(
        'Carrera',
        on_delete=models.PROTECT,  # PROTECT: No permite eliminar carrera si tiene materias
        related_name='materias',
        verbose_name='Carrera',
        help_text='Carrera a la que pertenece esta materia'
    )
    
    # REQUERIMIENTO: nombre (será único por carrera con la constraint)
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Materia',
        help_text='Nombre de la materia (único por carrera)'
    )
    
    codigo = models.CharField(
        max_length=20,
        verbose_name='Código de Materia',
        help_text='Código identificatorio (ej: MAT101, FIS201)'
    )
    
    # REQUERIMIENTO: cupo_maximo
    cupo_maximo = models.PositiveIntegerField(
        verbose_name='Cupo Máximo',
        help_text='Número máximo de estudiantes que pueden cursar la materia'
    )
    
    # Campos adicionales importantes para gestión académica
    año_carrera = models.PositiveIntegerField(
        default=1,
        verbose_name='Año de la Carrera',
        help_text='Año del plan de estudios en que se cursa (1, 2, 3, etc.)'
    )
    
    cuatrimestre = models.PositiveIntegerField(
        choices=[(1, '1° Cuatrimestre'), (2, '2° Cuatrimestre'), (0, 'Anual')],
        default=1,
        verbose_name='Cuatrimestre'
    )
    
    horas_semanales = models.PositiveIntegerField(
        default=4,
        verbose_name='Horas Semanales',
        help_text='Cantidad de horas de clase por semana'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Materia Activa',
        help_text='Indica si la materia está disponible para cursar'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada de la materia y sus objetivos'
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'
        ordering = ['carrera__nombre', 'año_carrera', 'cuatrimestre', 'nombre']
        
        # REQUERIMIENTO: UniqueConstraint en (carrera, nombre)
        constraints = [
            models.UniqueConstraint(
                fields=['carrera', 'nombre'],
                name='unique_materia_por_carrera',
                violation_error_message='Ya existe una materia con este nombre en la carrera seleccionada.'
            ),
            models.UniqueConstraint(
                fields=['carrera', 'codigo'],
                name='unique_codigo_por_carrera',
                violation_error_message='Ya existe una materia con este código en la carrera seleccionada.'
            ),
        ]
        
        indexes = [
            models.Index(fields=['carrera', 'año_carrera']),
            models.Index(fields=['activa']),
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.carrera.nombre})"
    
    @property
    def nombre_completo(self):
        """Retorna nombre completo con información contextual"""
        return f"{self.nombre} - {self.año_carrera}° año ({self.carrera.nombre})"
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        
        # Validar que el año no supere la duración de la carrera
        if self.carrera and self.año_carrera > self.carrera.duracion_anos:
            raise ValidationError({
                'año_carrera': f'El año no puede ser mayor a la duración de la carrera ({self.carrera.duracion_anos} años).'
            })
