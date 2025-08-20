"""
Mixins para control de acceso y permisos en la app users.

Este módulo contiene mixins reutilizables para controlar el acceso a vistas
basándose en roles de usuario, permisos y estados.

Mixins disponibles:
==================

1. RoleRequiredMixin: Control por roles específicos
2. AdminRequiredMixin: Solo administradores
3. ActiveUserRequiredMixin: Solo usuarios activos
4. PermissionRequiredMixin: Control por permisos Django

Uso en vistas:
==============

```python
from users.mixins import RoleRequiredMixin

class MiVistaProtegida(RoleRequiredMixin, CreateView):
    required_roles = ['ADMIN', 'PROFESOR']
    # resto de la vista...
```
"""

from django.contrib.auth.mixins import AccessMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden


class RoleRequiredMixin(AccessMixin):
    """
    Mixin que requiere que el usuario tenga uno de los roles especificados.
    
    Uso:
    ====
    
    ```python
    class MiVista(RoleRequiredMixin, TemplateView):
        required_roles = ['ADMIN']  # Solo administradores
        # o
        required_roles = ['ADMIN', 'PROFESOR']  # Admin o Profesor
    ```
    
    Atributos:
    ==========
    
    - required_roles: Lista de roles permitidos (requerido)
    - login_url: URL de redirección si no está autenticado
    - permission_denied_message: Mensaje personalizado de acceso denegado
    - redirect_field_name: Nombre del campo para redirección post-login
    
    Comportamiento:
    ===============
    
    1. Si el usuario no está autenticado → redirige a login
    2. Si está autenticado pero no tiene el rol → error 403
    3. Si tiene el rol requerido → permite acceso
    
    Mensajes automáticos:
    ====================
    
    - Error de acceso: Mensaje automático con roles requeridos
    - Logging de intentos de acceso no autorizado
    """
    
    required_roles = None
    permission_denied_message = "No tienes permisos para acceder a esta página."
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica permisos antes de ejecutar la vista.
        """
        # Verificar que required_roles esté definido
        if self.required_roles is None:
            raise ValueError(
                f"La vista {self.__class__.__name__} debe definir 'required_roles'. "
                f"Ejemplo: required_roles = ['ADMIN', 'PROFESOR']"
            )
        
        # Verificar autenticación
        if not request.user.is_authenticated:
            # Mensaje informativo para usuario no autenticado
            messages.info(
                request,
                "Debes iniciar sesión para acceder a esta página."
            )
            return self.handle_no_permission()
        
        # Verificar rol
        if not self.has_required_role(request.user):
            return self.handle_permission_denied(request)
        
        return super().dispatch(request, *args, **kwargs)
    
    def has_required_role(self, user):
        """
        Verifica si el usuario tiene alguno de los roles requeridos.
        
        Args:
            user: Instancia del usuario a verificar
            
        Returns:
            bool: True si tiene al menos uno de los roles requeridos
        """
        if not self.required_roles:
            return False
        
        # Convertir a lista si es string
        roles = self.required_roles
        if isinstance(roles, str):
            roles = [roles]
        
        # Verificar si tiene alguno de los roles
        return user.role in roles
    
    def handle_permission_denied(self, request):
        """
        Maneja el caso cuando el usuario no tiene el rol requerido.
        
        Args:
            request: HttpRequest object
            
        Returns:
            HttpResponse: Respuesta de error 403
        """
        user = request.user
        
        # Preparar información para el mensaje
        roles_requeridos = ', '.join(self.required_roles)
        rol_actual = user.get_role_display() if user.role else 'Sin rol'
        
        # Mensaje de error detallado
        mensaje_error = (
            f"⛔ Acceso denegado. "
            f"Rol requerido: {roles_requeridos}. "
            f"Tu rol actual: {rol_actual}."
        )
        
        messages.error(request, mensaje_error)
        
        # Log del intento de acceso no autorizado
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Acceso denegado a {request.path} - "
            f"Usuario: {user.email} (ID: {user.pk}) - "
            f"Rol: {user.role} - "
            f"Roles requeridos: {roles_requeridos}"
        )
        
        # Retornar error 403
        raise PermissionDenied(self.permission_denied_message)
    
    def get_required_roles_display(self):
        """
        Retorna los roles requeridos en formato legible.
        
        Returns:
            str: Roles formateados para mostrar al usuario
        """
        if not self.required_roles:
            return "Ninguno"
        
        from .models import User
        
        roles_display = []
        for role in self.required_roles:
            # Buscar el display name del rol
            for choice_value, choice_display in User.UserRole.choices:
                if choice_value == role:
                    roles_display.append(choice_display)
                    break
            else:
                roles_display.append(role)  # Fallback si no se encuentra
        
        return ', '.join(roles_display)


class AdminRequiredMixin(RoleRequiredMixin):
    """
    Mixin que requiere rol de administrador.
    
    Shortcut para RoleRequiredMixin con required_roles = ['ADMIN']
    
    Uso:
    ====
    
    ```python
    class VistaAdmin(AdminRequiredMixin, TemplateView):
        # Solo administradores pueden acceder
        pass
    ```
    """
    required_roles = ['ADMIN']


class ProfesorOrAdminMixin(RoleRequiredMixin):
    """
    Mixin que permite acceso a profesores y administradores.
    
    Uso común para funciones educativas.
    """
    required_roles = ['ADMIN', 'PROFESOR']


class ActiveUserRequiredMixin(AccessMixin):
    """
    Mixin que requiere que el usuario esté activo.
    
    Verifica que el usuario esté autenticado y tenga status 'ACTIVE'.
    
    Uso:
    ====
    
    ```python
    class MiVista(ActiveUserRequiredMixin, TemplateView):
        # Solo usuarios activos
        pass
    ```
    """
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica que el usuario esté activo antes de ejecutar la vista.
        """
        if not request.user.is_authenticated:
            messages.info(
                request,
                "Debes iniciar sesión para acceder a esta página."
            )
            return self.handle_no_permission()
        
        # Verificar que el usuario esté activo
        from .models import User
        if request.user.status != User.UserStatus.ACTIVE:
            messages.error(
                request,
                f"⛔ Tu cuenta está {request.user.get_status_display().lower()}. "
                f"Contacta al administrador para más información."
            )
            raise PermissionDenied("Usuario inactivo")
        
        return super().dispatch(request, *args, **kwargs)


class OwnerOrAdminMixin(AccessMixin):
    """
    Mixin que permite acceso solo al propietario del objeto o a administradores.
    
    Útil para vistas de perfil, edición de datos personales, etc.
    
    Uso:
    ====
    
    ```python
    class EditarPerfilView(OwnerOrAdminMixin, UpdateView):
        # Solo el propietario o admin pueden editar
        pass
    ```
    
    La vista debe tener un método get_object() que retorne el objeto a verificar.
    El objeto debe tener un campo 'user' o ser el mismo usuario.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica que el usuario sea el propietario o administrador.
        """
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Si es admin, permitir acceso
        if request.user.role == 'ADMIN':
            return super().dispatch(request, *args, **kwargs)
        
        # Obtener el objeto y verificar propietario
        try:
            obj = self.get_object()
            
            # Si el objeto tiene campo 'user'
            if hasattr(obj, 'user'):
                if obj.user != request.user:
                    messages.error(
                        request,
                        "⛔ Solo puedes acceder a tus propios datos."
                    )
                    raise PermissionDenied("No es el propietario")
            
            # Si el objeto ES el usuario
            elif obj != request.user:
                messages.error(
                    request,
                    "⛔ Solo puedes acceder a tu propio perfil."
                )
                raise PermissionDenied("No es el propietario")
            
        except AttributeError:
            # Si no hay get_object(), asumir que es válido
            pass
        
        return super().dispatch(request, *args, **kwargs)


# Alias para compatibilidad
StaffRequiredMixin = ProfesorOrAdminMixin


def role_required(roles):
    """
    Decorador para funciones que requieren roles específicos.
    
    Uso:
    ====
    
    ```python
    from users.mixins import role_required
    
    @role_required(['ADMIN'])
    def vista_admin(request):
        # Solo administradores
        pass
    
    @role_required(['ADMIN', 'PROFESOR'])
    def vista_staff(request):
        # Admin o Profesor
        pass
    ```
    
    Args:
        roles: Lista de roles permitidos o string con un solo rol
        
    Returns:
        function: Decorador que verifica roles
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.info(
                    request,
                    "Debes iniciar sesión para acceder a esta página."
                )
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            # Convertir a lista si es necesario
            required_roles = roles if isinstance(roles, list) else [roles]
            
            if request.user.role not in required_roles:
                roles_display = ', '.join(required_roles)
                messages.error(
                    request,
                    f"⛔ Acceso denegado. Rol requerido: {roles_display}. "
                    f"Tu rol: {request.user.get_role_display()}."
                )
                raise PermissionDenied("Rol insuficiente")
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator
