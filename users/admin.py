"""
Configuración del Django Admin para la app users.

Este módulo configura la interfaz de administración para los modelos
de la aplicación users, específicamente para el modelo User personalizado.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Configuración personalizada del admin para el modelo User.
    
    Adapta la interfaz de UserAdmin de Django para trabajar con nuestro
    modelo User personalizado que usa email en lugar de username.
    """
    
    # Configuración de la lista de usuarios
    list_display = (
        'email', 
        'get_full_name', 
        'dni', 
        'role_badge', 
        'is_active', 
        'must_change_password',
        'last_login',
        'date_joined'
    )
    
    list_filter = (
        'role', 
        'is_active', 
        'is_staff', 
        'must_change_password',
        'date_joined',
        'last_login'
    )
    
    search_fields = ('email', 'first_name', 'last_name', 'dni')
    
    ordering = ('last_name', 'first_name')
    
    # Configuración de los fieldsets para el formulario de edición
    fieldsets = (
        ('Información Básica', {
            'fields': ('email', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'dni')
        }),
        ('Configuración del Usuario', {
            'fields': ('role', 'must_change_password'),
            'classes': ('collapse',)
        }),
        ('Permisos', {
            'fields': (
                'is_active', 
                'is_staff', 
                'is_superuser',
                'groups', 
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Configuración para añadir usuarios
    add_fieldsets = (
        ('Información Básica', {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
        ('Información Personal', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'dni'),
        }),
        ('Configuración del Usuario', {
            'classes': ('wide',),
            'fields': ('role', 'must_change_password'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    
    # Configuración de filtros
    list_per_page = 25
    list_max_show_all = 100
    
    def role_badge(self, obj):
        """
        Muestra el rol del usuario como un badge colorizado.
        
        Args:
            obj: Instancia del modelo User
            
        Returns:
            str: HTML con el badge del rol
        """
        colors = {
            User.UserRole.ADMIN: 'danger',
            User.UserRole.ALUMNO: 'success',
            User.UserRole.INVITADO: 'secondary',
        }
        
        color = colors.get(obj.role, 'secondary')
        icon = obj.get_role_display_icon()
        
        return format_html(
            '<span class="badge badge-{} text-white">'
            '<i class="{}"></i> {}'
            '</span>',
            color,
            icon,
            obj.get_role_display()
        )
    
    role_badge.short_description = 'Rol'
    role_badge.admin_order_field = 'role'
    
    def get_full_name(self, obj):
        """
        Obtiene el nombre completo del usuario para mostrar en la lista.
        
        Args:
            obj: Instancia del modelo User
            
        Returns:
            str: Nombre completo del usuario
        """
        return obj.get_full_name()
    
    get_full_name.short_description = 'Nombre Completo'
    get_full_name.admin_order_field = 'first_name'
    
    # Acciones personalizadas
    actions = ['make_active', 'make_inactive', 'force_password_change', 'remove_password_change']
    
    def make_active(self, request, queryset):
        """Activa los usuarios seleccionados."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'{updated} usuario(s) activado(s) correctamente.'
        )
    make_active.short_description = "Activar usuarios seleccionados"
    
    def make_inactive(self, request, queryset):
        """Desactiva los usuarios seleccionados."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} usuario(s) desactivado(s) correctamente.'
        )
    make_inactive.short_description = "Desactivar usuarios seleccionados"
    
    def force_password_change(self, request, queryset):
        """Fuerza el cambio de contraseña en los usuarios seleccionados."""
        updated = queryset.update(must_change_password=True)
        self.message_user(
            request, 
            f'{updated} usuario(s) deberán cambiar su contraseña en el próximo inicio de sesión.'
        )
    force_password_change.short_description = "Forzar cambio de contraseña"
    
    def remove_password_change(self, request, queryset):
        """Remueve el requisito de cambio de contraseña."""
        updated = queryset.update(must_change_password=False)
        self.message_user(
            request, 
            f'{updated} usuario(s) ya no necesitan cambiar su contraseña.'
        )
    remove_password_change.short_description = "Remover requisito de cambio de contraseña"
