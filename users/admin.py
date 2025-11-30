from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuración del admin para el modelo User personalizado.
    """
    list_display = ['email', 'first_name', 'last_name', 'dni', 'role', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff', 'must_change_password']
    search_fields = ['email', 'first_name', 'last_name', 'dni']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'dni', 'phone', 'address')}),
        ('Permisos', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Cambio de Contraseña', {'fields': ('must_change_password', 'password_changed_at')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'dni', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
