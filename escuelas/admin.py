"""
Configuración del Admin de Django para la app escuelas.

Este módulo configura la interfaz administrativa para los modelos
Carrera y Materia con funcionalidades avanzadas.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Carrera, Materia


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    """Admin optimizado para Carrera"""
    
    list_display = ['nombre', 'codigo', 'duracion_anos', 'estado_badge', 'total_materias', 'fecha_creacion']
    list_filter = ['activa', 'duracion_anos', 'fecha_creacion']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo')
        }),
        ('Configuración', {
            'fields': ('duracion_anos', 'activa', 'descripcion')
        }),
    )
    
    def estado_badge(self, obj):
        """Muestra estado con colores"""
        if obj.activa:
            return format_html('<span style="color: green;">✅ Activa</span>')
        return format_html('<span style="color: red;">❌ Inactiva</span>')
    estado_badge.short_description = 'Estado'


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    """Admin optimizado para Materia"""
    
    list_display = ['nombre', 'codigo', 'carrera', 'año_carrera', 'cuatrimestre', 'cupo_maximo', 'estado_badge']
    list_filter = ['carrera', 'activa', 'año_carrera', 'cuatrimestre']
    search_fields = ['nombre', 'codigo', 'carrera__nombre']
    ordering = ['carrera__nombre', 'año_carrera', 'nombre']
    list_select_related = ['carrera']
    
    fieldsets = (
        ('Información Básica', {
            'fields': (('nombre', 'codigo'), 'carrera')
        }),
        ('Configuración Académica', {
            'fields': (('año_carrera', 'cuatrimestre'), ('cupo_maximo', 'horas_semanales'), 'activa')
        }),
        ('Descripción', {
            'fields': ('descripcion',),
            'classes': ('collapse',)
        }),
    )
    
    def estado_badge(self, obj):
        """Estado de la materia"""
        if obj.activa:
            return format_html('<span style="color: green;">✅ Activa</span>')
        return format_html('<span style="color: red;">❌ Inactiva</span>')
    estado_badge.short_description = 'Estado'
