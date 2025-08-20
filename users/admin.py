"""
Configuración del Django Admin para la app users.

Este módulo configura la interfaz de administración para los modelos
de la aplicación users, específicamente para el modelo User personalizado.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, UserActivityLog


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
        'status_badge',
        'is_active', 
        'must_change_password',
        'failed_login_attempts',
        'last_login',
        'date_joined'
    )
    
    list_filter = (
        'role',
        'status', 
        'is_active', 
        'is_staff', 
        'must_change_password',
        'date_joined',
        'last_login',
        'password_changed_at',
    )
    
    search_fields = ('email', 'first_name', 'last_name', 'dni', 'phone')
    
    ordering = ('last_name', 'first_name')
    
    # Configuración de los fieldsets para el formulario de edición
    fieldsets = (
        ('Información Básica', {
            'fields': ('email', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'dni', 'phone', 'address', 'birth_date')
        }),
        ('Configuración del Usuario', {
            'fields': ('role', 'status', 'must_change_password'),
            'classes': ('collapse',)
        }),
        ('Información de Seguridad', {
            'fields': (
                'failed_login_attempts', 
                'last_failed_login',
                'password_changed_at',
                'last_password_reset'
            ),
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
        ('Auditoría', {
            'fields': ('created_by', 'last_login', 'date_joined', 'uuid'),
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
            'fields': ('first_name', 'last_name', 'dni', 'phone', 'birth_date'),
        }),
        ('Configuración del Usuario', {
            'classes': ('wide',),
            'fields': ('role', 'status', 'must_change_password'),
        }),
    )
    
    readonly_fields = (
        'uuid', 
        'last_login', 
        'date_joined', 
        'password_changed_at',
        'last_password_reset',
        'failed_login_attempts',
        'last_failed_login'
    )
    
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
            User.UserRole.PROFESOR: 'primary',
            User.UserRole.ALUMNO: 'success',
            User.UserRole.PADRE: 'info',
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
    
    def status_badge(self, obj):
        """
        Muestra el estado del usuario como un badge colorizado.
        
        Args:
            obj: Instancia del modelo User
            
        Returns:
            str: HTML con el badge del estado
        """
        colors = {
            User.UserStatus.ACTIVE: 'success',
            User.UserStatus.INACTIVE: 'secondary',
            User.UserStatus.SUSPENDED: 'danger',
            User.UserStatus.PENDING: 'warning',
        }
        
        color = colors.get(obj.status, 'secondary')
        icon = obj.get_status_display_icon()
        
        return format_html(
            '<span class="badge badge-{} text-white">'
            '<i class="{}"></i> {}'
            '</span>',
            color,
            icon,
            obj.get_status_display()
        )
    
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'
    
    def get_full_name(self, obj):
        """
        Obtiene el nombre completo del usuario para mostrar en la lista.
        
        Args:
            obj: Instancia del modelo User
            
        Returns:
            str: Nombre completo del usuario
        """
        full_name = obj.get_full_name()
        if obj.get_age():
            return f"{full_name} ({obj.get_age()} años)"
        return full_name
    
    get_full_name.short_description = 'Nombre Completo'
    get_full_name.admin_order_field = 'first_name'
    
    # Acciones personalizadas
    actions = [
        'make_active', 
        'make_inactive', 
        'force_password_change', 
        'remove_password_change',
        'activate_users',
        'suspend_users',
        'reset_failed_attempts'
    ]
    
    def make_active(self, request, queryset):
        """Activa los usuarios seleccionados."""
        updated = queryset.update(is_active=True, status=User.UserStatus.ACTIVE)
        self.message_user(
            request, 
            f'{updated} usuario(s) activado(s) correctamente.'
        )
    make_active.short_description = "Activar usuarios seleccionados"
    
    def make_inactive(self, request, queryset):
        """Desactiva los usuarios seleccionados."""
        updated = queryset.update(is_active=False, status=User.UserStatus.INACTIVE)
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
    
    def activate_users(self, request, queryset):
        """Activa usuarios usando el método del modelo."""
        count = 0
        for user in queryset:
            user.activate_user()
            count += 1
        self.message_user(
            request, 
            f'{count} usuario(s) activado(s) y aprobado(s) correctamente.'
        )
    activate_users.short_description = "Activar y aprobar usuarios seleccionados"
    
    def suspend_users(self, request, queryset):
        """Suspende usuarios usando el método del modelo."""
        count = 0
        for user in queryset:
            user.suspend_user("Suspendido desde admin")
            count += 1
        self.message_user(
            request, 
            f'{count} usuario(s) suspendido(s) correctamente.'
        )
    suspend_users.short_description = "Suspender usuarios seleccionados"
    
    def reset_failed_attempts(self, request, queryset):
        """Resetea los intentos fallidos de login."""
        count = 0
        for user in queryset:
            user.reset_failed_login_attempts()
            count += 1
        self.message_user(
            request, 
            f'Intentos fallidos reseteados para {count} usuario(s).'
        )
    reset_failed_attempts.short_description = "Resetear intentos fallidos de login"


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo UserActivityLog.
    """
    
    list_display = (
        'user',
        'activity_type',
        'timestamp',
        'ip_address',
        'get_user_agent_short'
    )
    
    list_filter = (
        'activity_type',
        'timestamp',
        'user__role',
    )
    
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'ip_address',
    )
    
    readonly_fields = (
        'user',
        'activity_type',
        'timestamp',
        'ip_address',
        'user_agent',
        'details'
    )
    
    ordering = ('-timestamp',)
    
    list_per_page = 50
    
    def get_user_agent_short(self, obj):
        """Devuelve una versión corta del user agent."""
        if obj.user_agent:
            return obj.user_agent[:50] + "..." if len(obj.user_agent) > 50 else obj.user_agent
        return "-"
    
    get_user_agent_short.short_description = 'User Agent'
    
    def has_add_permission(self, request):
        """Los logs no se pueden agregar manualmente."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Los logs no se pueden modificar."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo los superusuarios pueden eliminar logs."""
        return request.user.is_superuser


# Configuración personalizada del sitio admin
admin.site.site_header = "Sistema Escolar - Administración"
admin.site.site_title = "Admin Sistema Escolar"
admin.site.index_title = "Panel de Administración"
