from django.contrib import admin
from .models import Inscripcion


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Inscripcion.
    """
    list_display = ['alumno', 'materia', 'fecha_inscripcion', 'estado']
    list_filter = ['estado', 'fecha_inscripcion', 'materia__carrera']
    search_fields = ['alumno__legajo', 'alumno__first_name', 'alumno__last_name', 'materia__nombre']
    ordering = ['-fecha_inscripcion']
    date_hierarchy = 'fecha_inscripcion'
