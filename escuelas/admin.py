from django.contrib import admin
from .models import Carrera, Materia


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Carrera.
    """
    list_display = ['codigo', 'nombre', 'duracion_años', 'activa']
    list_filter = ['activa', 'duracion_años']
    search_fields = ['codigo', 'nombre']
    ordering = ['nombre']


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Materia.
    """
    list_display = ['codigo', 'nombre', 'carrera', 'año_carrera', 'cupo_maximo', 'inscriptos_actuales', 'activa']
    list_filter = ['carrera', 'año_carrera', 'activa']
    search_fields = ['codigo', 'nombre', 'carrera__nombre']
    ordering = ['carrera', 'año_carrera', 'nombre']
    
    def inscriptos_actuales(self, obj):
        return obj.inscriptos_actuales()
    inscriptos_actuales.short_description = 'Inscriptos'
