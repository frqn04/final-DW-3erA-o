"""
Middleware personalizado para la app users.

Este módulo contiene middleware específico para funcionalidades de usuarios,
incluyendo middleware para:
- Forzar cambio de contraseña en el primer login
- Logging de actividad de usuarios
- Verificaciones de seguridad automáticas
- Control de sesiones y timeouts
"""

import logging
from datetime import datetime, timedelta
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.auth import logout
from django.conf import settings
from django.core.exceptions import PermissionDenied

logger = logging.getLogger('users.middleware')


class ForcePasswordChangeMiddleware(MiddlewareMixin):
    """
    Middleware que fuerza a los usuarios a cambiar su contraseña en el primer login.
    
    ¿Cómo funciona?
    ---------------
    Este middleware intercepta todas las peticiones HTTP antes de que lleguen a las vistas.
    Si detecta que un usuario autenticado tiene el flag 'password_change_required=True',
    automáticamente lo redirige a la vista de cambio de contraseña, impidiendo que
    acceda a cualquier otra parte del sistema hasta que actualice su contraseña.
    
    ¿Por qué es importante?
    ----------------------
    - SEGURIDAD: Fuerza a los usuarios a cambiar contraseñas temporales o por defecto
    - CUMPLIMIENTO: Ayuda a cumplir políticas de seguridad organizacionales
    - EXPERIENCIA: Guía automáticamente al usuario sin confusión
    - PREVENCIÓN: Evita que usuarios con contraseñas débiles accedan al sistema
    """
    
    def process_request(self, request):
        """
        Intercepta cada petición HTTP para verificar el estado del usuario.
        
        El proceso de verificación sigue estos pasos:
        1. ¿El usuario está autenticado? Si no → continuar normalmente
        2. ¿El usuario tiene flag de cambio requerido? Si no → continuar
        3. ¿La URL actual está en la lista de excepciones? Si sí → permitir acceso
        4. Si llegamos aquí → redirigir a cambio de contraseña
        
        Args:
            request: El objeto HttpRequest con la petición actual
            
        Returns:
            HttpResponse: Redirección si se requiere cambio de contraseña
            None: Si debe continuar el procesamiento normal
        """
        
        # PASO 1: Verificar autenticación
        if not request.user.is_authenticated:
            return None
        
        # PASO 2: Verificar atributos necesarios (compatibilidad con diferentes modelos User)
        password_change_required = False
        
        # Verificar diferentes nombres de atributos para compatibilidad
        if hasattr(request.user, 'password_change_required'):
            password_change_required = request.user.password_change_required
        elif hasattr(request.user, 'must_change_password'):
            password_change_required = request.user.must_change_password
        
        if not password_change_required:
            return None
        
        # PASO 3: Definir URLs de excepción
        current_path = request.path_info
        
        # URLs que SIEMPRE deben estar accesibles
        exempt_paths = [
            '/admin/',                    # Panel de administración
            '/login/',                   # Página de login
            '/logout/',                  # Página de logout  
            '/static/',                  # Archivos estáticos
            '/media/',                   # Archivos de medios
            '/favicon.ico',              # Icono del navegador
            '/api/health/',              # Health checks
        ]
        
        # URLs específicas que también deben estar exentas
        try:
            exempt_named_urls = [
                'users:login',
                'users:logout', 
                'users:change_password_first_login',
                'admin:index',
                'admin:login',
                'admin:logout',
            ]
            
            for url_name in exempt_named_urls:
                try:
                    url_path = reverse(url_name)
                    exempt_paths.append(url_path)
                except:
                    pass  # Ignorar URLs que no existen
                    
        except Exception as e:
            logger.warning(f"Error resolviendo URLs exentas: {e}")
        
        # PASO 4: Verificar si la ruta actual está exenta
        for exempt_path in exempt_paths:
            if current_path.startswith(exempt_path):
                return None
        
        # PASO 5: Verificar si ya está en la página de cambio de contraseña
        try:
            password_change_url = reverse('users:change_password_first_login')
            if current_path == password_change_url:
                return None
        except Exception as e:
            logger.warning(
                f"ForcePasswordChangeMiddleware: No se pudo resolver la URL "
                f"'users:change_password_first_login'. Error: {e}"
            )
            # Intentar URL alternativa
            try:
                password_change_url = reverse('change_password_first_login')
                if current_path == password_change_url:
                    return None
            except:
                pass
        
        # PASO 6: Registrar intento de acceso no autorizado
        logger.info(
            f"Usuario {request.user.email} intentó acceder a {current_path} "
            f"pero debe cambiar contraseña primero"
        )
        
        # PASO 7: Mostrar mensaje informativo
        if not request.session.get('password_change_message_shown', False):
            messages.warning(
                request,
                '⚠️ Debes cambiar tu contraseña antes de continuar usando el sistema. '
                'Por seguridad, se requiere que actualices tu contraseña temporal.'
            )
            request.session['password_change_message_shown'] = True
        
        # PASO 8: Redirigir a la página de cambio de contraseña
        try:
            return redirect('users:change_password_first_login')
        except Exception:
            try:
                return redirect('change_password_first_login')
            except Exception as e:
                logger.error(
                    f"ForcePasswordChangeMiddleware: Error al redirigir usuario "
                    f"{request.user.email} a cambio de contraseña. Error: {e}"
                )
                return None


class UserActivityMiddleware(MiddlewareMixin):
    """
    Middleware para registrar actividad de usuarios en el sistema.
    
    Registra automáticamente:
    - Páginas visitadas por usuarios autenticados
    - Tiempo de actividad
    - IPs utilizadas
    - Acciones importantes del sistema
    """
    
    def process_request(self, request):
        """Registra la actividad del usuario al inicio de cada request."""
        if not request.user.is_authenticated:
            return None
        
        # Actualizar última actividad
        request.user.last_activity = timezone.now()
        
        # Obtener IP del cliente
        client_ip = self._get_client_ip(request)
        
        # Actualizar IP si es diferente
        if hasattr(request.user, 'last_login_ip') and request.user.last_login_ip != client_ip:
            request.user.last_login_ip = client_ip
        
        # Guardar cambios (solo los campos necesarios para optimizar)
        try:
            fields_to_update = ['last_activity']
            if hasattr(request.user, 'last_login_ip'):
                fields_to_update.append('last_login_ip')
            
            request.user.save(update_fields=fields_to_update)
        except Exception as e:
            logger.error(f"Error actualizando actividad de usuario: {e}")
        
        return None
    
    def process_response(self, request, response):
        """Registra actividad específica después del procesamiento."""
        if not request.user.is_authenticated:
            return response
        
        # Registrar acceso a páginas importantes
        path = request.path_info
        method = request.method
        
        # Páginas que queremos registrar específicamente
        important_paths = [
            '/admin/',
            '/users/',
            '/escuelas/',
            '/students/',
            '/enrollments/',
        ]
        
        should_log = any(path.startswith(imp_path) for imp_path in important_paths)
        
        if should_log and method in ['GET', 'POST', 'PUT', 'DELETE']:
            try:
                from .models import UserActivityLog
                
                # Evitar spam de logs
                last_log_key = f'last_activity_log_{request.user.id}_{path}'
                last_log_time = request.session.get(last_log_key)
                
                now = timezone.now()
                if not last_log_time or (now - datetime.fromisoformat(last_log_time)).seconds > 60:
                    UserActivityLog.objects.create(
                        user=request.user,
                        action=f'{method.lower()}_page_access',
                        details=f'Accessed {path}',
                        ip_address=self._get_client_ip(request)
                    )
                    request.session[last_log_key] = now.isoformat()
                    
            except Exception as e:
                logger.error(f"Error creando log de actividad: {e}")
        
        return response
    
    def _get_client_ip(self, request):
        """Obtiene la IP real del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


class SecurityCheckMiddleware(MiddlewareMixin):
    """
    Middleware para verificaciones de seguridad automáticas.
    
    Incluye:
    - Verificación de cuentas bloqueadas
    - Control de sesiones inactivas
    - Verificación de estado de cuenta
    """
    
    # Configuración de timeouts (en minutos)
    SESSION_TIMEOUT = getattr(settings, 'SESSION_TIMEOUT_MINUTES', 120)
    ADMIN_SESSION_TIMEOUT = getattr(settings, 'ADMIN_SESSION_TIMEOUT_MINUTES', 60)
    
    def process_request(self, request):
        """Verifica seguridad del usuario en cada request."""
        if not request.user.is_authenticated:
            return None
        
        user = request.user
        
        # Verificar si la cuenta está bloqueada
        if self._is_account_blocked(user):
            logger.warning(f"Acceso denegado para cuenta bloqueada: {user.email}")
            logout(request)
            messages.error(
                request, 
                'Tu cuenta ha sido bloqueada. Contacta al administrador.'
            )
            return redirect('users:login')
        
        # Verificar estado de la cuenta
        if hasattr(user, 'status') and user.status != user.UserStatus.ACTIVE:
            logger.warning(f"Acceso denegado para cuenta inactiva: {user.email}")
            logout(request)
            messages.error(
                request,
                'Tu cuenta no está activa. Contacta al administrador.'
            )
            return redirect('users:login')
        
        # Verificar timeout de sesión
        if self._is_session_expired(request):
            logger.info(f"Sesión expirada para usuario: {user.email}")
            logout(request)
            messages.info(
                request,
                'Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.'
            )
            return redirect('users:login')
        
        return None
    
    def _is_account_blocked(self, user):
        """Verifica si la cuenta está bloqueada."""
        if hasattr(user, 'account_locked_until') and user.account_locked_until:
            return timezone.now() < user.account_locked_until
        return False
    
    def _is_session_expired(self, request):
        """Verifica si la sesión ha expirado por inactividad."""
        if not hasattr(request.user, 'last_activity'):
            return False
        
        # Determinar timeout según tipo de usuario
        timeout_minutes = self.ADMIN_SESSION_TIMEOUT if request.user.is_staff else self.SESSION_TIMEOUT
        
        last_activity = request.user.last_activity
        if not last_activity:
            return False
        
        time_since_activity = timezone.now() - last_activity
        return time_since_activity.total_seconds() > (timeout_minutes * 60)
