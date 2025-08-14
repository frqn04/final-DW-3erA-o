"""
Middleware personalizado para la app users.

Este módulo contiene middleware específico para funcionalidades de usuarios,
incluyendo el middleware para forzar cambio de contraseña en el primer login.
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin


class ForcePasswordChangeMiddleware(MiddlewareMixin):
    """
    Middleware que fuerza a los usuarios a cambiar su contraseña en el primer login.
    
    ¿Cómo funciona?
    ---------------
    Este middleware intercepta todas las peticiones HTTP antes de que lleguen a las vistas.
    Si detecta que un usuario autenticado tiene el flag 'must_change_password=True',
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
        2. ¿El usuario tiene el flag must_change_password? Si no → continuar
        3. ¿La URL actual está en la lista de excepciones? Si sí → permitir acceso
        4. Si llegamos aquí → redirigir a cambio de contraseña
        
        Args:
            request: El objeto HttpRequest con la petición actual
            
        Returns:
            HttpResponse: Redirección si se requiere cambio de contraseña
            None: Si debe continuar el procesamiento normal
        """
        
        # PASO 1: Verificar autenticación
        # Si el usuario no está autenticado, no necesitamos hacer nada
        if not request.user.is_authenticated:
            return None
        
        # PASO 2: Verificar si el modelo User tiene el atributo must_change_password
        # Esto previene errores si se usa este middleware con otros modelos User
        if not hasattr(request.user, 'must_change_password'):
            return None
        
        # PASO 3: Verificar si el usuario necesita cambiar contraseña
        # Si must_change_password es False, el usuario ya cambió su contraseña
        if not request.user.must_change_password:
            return None
        
        # PASO 4: Definir URLs de excepción
        # Estas rutas deben estar siempre accesibles para evitar loops infinitos
        current_path = request.path_info
        
        # URLs que SIEMPRE deben estar accesibles
        exempt_paths = [
            '/admin/',                    # Panel de administración
            '/login/',                   # Página de login
            '/logout/',                  # Página de logout  
            '/static/',                  # Archivos estáticos (CSS, JS, imágenes)
            '/media/',                   # Archivos de medios subidos por usuarios
        ]
        
        # PASO 5: Verificar si la ruta actual está exenta
        for exempt_path in exempt_paths:
            if current_path.startswith(exempt_path):
                return None
        
        # PASO 6: Verificar si ya está en la página de cambio de contraseña
        try:
            # Intentar obtener la URL nombrada de cambio de contraseña
            password_change_url = reverse('users:change_password_first_login')
            
            if current_path == password_change_url:
                # Ya está en la página correcta, permitir acceso
                return None
                
        except Exception as e:
            # Si no se puede resolver la URL, registrar el error pero permitir continuar
            # Esto evita que el sitio se rompa si la URL no está configurada
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"ForcePasswordChangeMiddleware: No se pudo resolver la URL "
                f"'users:change_password_first_login'. Error: {e}"
            )
            return None
        
        # PASO 7: Mostrar mensaje informativo al usuario
        # Solo mostrar el mensaje si no lo hemos mostrado ya en esta sesión
        if not request.session.get('password_change_message_shown', False):
            messages.warning(
                request,
                '⚠️ Debes cambiar tu contraseña antes de continuar usando el sistema. '
                'Por seguridad, se requiere que actualices tu contraseña temporal.'
            )
            # Marcar que ya mostramos el mensaje para evitar spam
            request.session['password_change_message_shown'] = True
        
        # PASO 8: Redirigir a la página de cambio de contraseña
        try:
            return redirect('users:change_password_first_login')
        except Exception as e:
            # Si falla la redirección, permitir continuar y registrar el error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"ForcePasswordChangeMiddleware: Error al redirigir usuario {request.user.email} "
                f"a cambio de contraseña. Error: {e}"
            )
            return None
