from django.contrib import admin
from .models import Alumno


class InscripcionInline(admin.TabularInline):
    """
    Inline para mostrar las inscripciones del alumno en el admin.
    """
    from enrollments.models import Inscripcion
    model = Inscripcion
    extra = 0
    readonly_fields = ['fecha_inscripcion']
    fields = ['materia', 'estado', 'fecha_inscripcion', 'observaciones']
    can_delete = False


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Alumno.
    """
    list_display = ['legajo', 'last_name', 'first_name', 'dni', 'carrera', 'activo', 'fecha_ingreso', 'get_inscripciones_count']
    list_filter = ['carrera', 'activo', 'fecha_ingreso']
    search_fields = ['legajo', 'first_name', 'last_name', 'dni', 'email']
    ordering = ['last_name', 'first_name']
    readonly_fields = ['legajo']
    inlines = [InscripcionInline]
    
    def get_inscripciones_count(self, obj):
        """Muestra la cantidad de inscripciones del alumno"""
        return obj.inscripciones.count()
    get_inscripciones_count.short_description = 'Inscripciones'
