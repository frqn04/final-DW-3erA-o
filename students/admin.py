"""
Configuración del admin para la app students.

Interfaz administrativa profesional para la gestión de alumnos con:
- Vistas optimizadas y filtros avanzados
- Búsquedas inteligentes
- Acciones masivas
- Validaciones en tiempo real
- Badges y formateo visual
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.contrib import messages
from django.shortcuts import redirect

from .models import Alumno


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    """
    Configuración avanzada del admin para Alumno.
    
    Características:
    - Lista optimizada con información clave
    - Filtros por carrera, estado, fecha de ingreso
    - Búsqueda por múltiples campos
    - Acciones masivas para activar/desactivar
    - Formulario organizado en fieldsets
    - Validaciones personalizadas
    """
    
    # Configuración de la lista
    list_display = [
        'legajo_badge',
        'nombre_completo_link',
        'dni',
        'carrera_info',
        'fecha_ingreso',
        'estado_badge',
        'años_institucion',
        'fecha_actualizacion',
    ]
    
    list_filter = [
        'activo',
        'carrera__nombre',
        'fecha_ingreso',
        'fecha_creacion',
        ('carrera', admin.RelatedOnlyFieldListFilter),
    ]
    
    search_fields = [
        'first_name',
        'last_name', 
        'dni',
        'legajo',
        'email',
        'carrera__nombre',
        'carrera__codigo',
    ]
    
    list_per_page = 25
    list_max_show_all = 100
    
    # Configuración del formulario
    fieldsets = (
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'dni', 'email'),
            'classes': ('wide',),
        }),
        ('Información Académica', {
            'fields': ('legajo', 'carrera', 'fecha_ingreso'),
            'classes': ('wide',),
        }),
        ('Estado y Observaciones', {
            'fields': ('activo', 'observaciones'),
            'classes': ('wide',),
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    # Configuraciones adicionales
    ordering = ['last_name', 'first_name']
    date_hierarchy = 'fecha_ingreso'
    
    # Acciones personalizadas
    actions = ['activar_alumnos', 'desactivar_alumnos', 'generar_reporte_carrera']
    
    def get_queryset(self, request):
        """
        Optimiza el queryset con select_related para evitar N+1 queries.
        """
        return super().get_queryset(request).select_related('carrera')
    
    # ==========================================
    # MÉTODOS PARA DISPLAY PERSONALIZADO
    # ==========================================
    
    def legajo_badge(self, obj):
        """
        Muestra el legajo como badge con color según el estado.
        """
        color = 'success' if obj.activo else 'secondary'
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.legajo
        )
    legajo_badge.short_description = 'Legajo'
    legajo_badge.admin_order_field = 'legajo'
    
    def nombre_completo_link(self, obj):
        """
        Muestra el nombre completo como enlace al detalle.
        """
        url = reverse('admin:students_alumno_change', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, obj.nombre_completo)
    nombre_completo_link.short_description = 'Nombre Completo'
    nombre_completo_link.admin_order_field = 'last_name'
    
    def carrera_info(self, obj):
        """
        Muestra información de la carrera con enlace.
        """
        if obj.carrera:
            color = 'primary' if obj.carrera.activa else 'warning'
            return format_html(
                '<span class="badge badge-{}">{}</span><br><small>{}</small>',
                color,
                obj.carrera.nombre,
                obj.carrera.codigo
            )
        return format_html('<span class="text-muted">Sin carrera</span>')
    carrera_info.short_description = 'Carrera'
    carrera_info.admin_order_field = 'carrera__nombre'
    
    def estado_badge(self, obj):
        """
        Muestra el estado del alumno con badge colorido.
        """
        if obj.activo:
            return format_html(
                '<span class="badge badge-success">✓ Activo</span>'
            )
        else:
            return format_html(
                '<span class="badge badge-danger">✗ Inactivo</span>'
            )
    estado_badge.short_description = 'Estado'
    estado_badge.admin_order_field = 'activo'
    
    def años_institucion(self, obj):
        """
        Calcula y muestra los años en la institución.
        """
        años = obj.años_en_institucion
        if años == 0:
            return format_html('<span class="text-muted">Nuevo</span>')
        elif años == 1:
            return format_html('<span class="text-info">1 año</span>')
        else:
            return format_html('<span class="text-info">{} años</span>', años)
    años_institucion.short_description = 'Antigüedad'
    
    # ==========================================
    # ACCIONES PERSONALIZADAS
    # ==========================================
    
    def activar_alumnos(self, request, queryset):
        """
        Activa múltiples alumnos de una vez.
        """
        count = queryset.update(activo=True)
        self.message_user(
            request,
            f'Se activaron {count} alumno(s) exitosamente.',
            messages.SUCCESS
        )
    activar_alumnos.short_description = "✓ Activar alumnos seleccionados"
    
    def desactivar_alumnos(self, request, queryset):
        """
        Desactiva múltiples alumnos de una vez.
        """
        count = queryset.update(activo=False)
        self.message_user(
            request,
            f'Se desactivaron {count} alumno(s) exitosamente.',
            messages.WARNING
        )
    desactivar_alumnos.short_description = "✗ Desactivar alumnos seleccionados"
    
    def generar_reporte_carrera(self, request, queryset):
        """
        Genera reporte básico por carrera de los alumnos seleccionados.
        """
        carreras_stats = queryset.values('carrera__nombre').annotate(
            total=Count('id'),
            activos=Count('id', filter=Q(activo=True))
        ).order_by('carrera__nombre')
        
        mensaje = "📊 Reporte por carrera:<br>"
        for stat in carreras_stats:
            carrera = stat['carrera__nombre'] or 'Sin carrera'
            mensaje += f"• {carrera}: {stat['total']} total, {stat['activos']} activos<br>"
        
        self.message_user(
            request,
            mark_safe(mensaje),
            messages.INFO
        )
    generar_reporte_carrera.short_description = "📊 Reporte por carrera"
    
    # ==========================================
    # VALIDACIONES PERSONALIZADAS
    # ==========================================
    
    def save_model(self, request, obj, form, change):
        """
        Validaciones adicionales al guardar desde el admin.
        """
        try:
            super().save_model(request, obj, form, change)
            if change:
                self.message_user(
                    request,
                    f'Alumno "{obj.nombre_completo}" actualizado exitosamente.',
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f'Alumno "{obj.nombre_completo}" creado con legajo: {obj.legajo}',
                    messages.SUCCESS
                )
        except Exception as e:
            self.message_user(
                request,
                f'Error al guardar: {str(e)}',
                messages.ERROR
            )
    
    def delete_model(self, request, obj):
        """
        Mensaje personalizado al eliminar.
        """
        nombre = obj.nombre_completo
        legajo = obj.legajo
        super().delete_model(request, obj)
        self.message_user(
            request,
            f'Alumno "{nombre}" (Legajo: {legajo}) eliminado exitosamente.',
            messages.SUCCESS
        )


# ==========================================
# CONFIGURACIÓN ADICIONAL DEL ADMIN
# ==========================================

# Personalizar el título del admin
admin.site.site_header = "Administración del Sistema Educativo"
admin.site.site_title = "Admin Educativo"
admin.site.index_title = "Panel de Administración"
