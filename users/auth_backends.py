"""
Backends de autenticación personalizados para la app users.

Este módulo contiene backends de autenticación alternativos que permiten
diferentes métodos de autenticación además del método estándar de Django.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


User = get_user_model()


class EmailDNIBackend(ModelBackend):
    """
    Backend de autenticación que requiere email, DNI y contraseña.
    
    Este backend personalizado permite autenticación más segura requiriendo
    que el usuario proporcione tanto su email como su DNI registrado,
    además de la contraseña. Esto añade una capa extra de seguridad.
    """
    
    def authenticate(self, request, username=None, password=None, dni=None, **kwargs):
        """
        Autentica a un usuario usando email, DNI y contraseña.
        
        Args:
            request: La petición HTTP actual
            username: El email del usuario (se usa 'username' por compatibilidad)
            password: La contraseña del usuario
            dni: El DNI que debe coincidir con el registrado
            **kwargs: Argumentos adicionales
            
        Returns:
            User: El usuario autenticado si las credenciales son válidas
            None: Si las credenciales son inválidas o falta información
        """
        
        # Paso 1: Validar que se proporcionen todos los datos requeridos
        if not username or not password or not dni:
            # Si falta algún campo requerido, rechazar la autenticación
            return None
        
        try:
            # Paso 2: Buscar el usuario por email
            # Usamos get() en lugar de filter() para obtener exactamente un usuario
            # o lanzar una excepción si no existe o hay múltiples (lo cual no debería pasar)
            user = User.objects.get(email__iexact=username.lower())
            
        except User.DoesNotExist:
            # Paso 3a: Si el email no existe en la base de datos
            # Ejecutamos check_password de todas formas para evitar timing attacks
            # (ataques que miden el tiempo de respuesta para determinar si un email existe)
            User().check_password(password)
            return None
            
        except User.MultipleObjectsReturned:
            # Paso 3b: Si hay múltiples usuarios con el mismo email (error de integridad)
            # Esto no debería pasar debido a la restricción unique=True en el email
            return None
        
        # Paso 4: Verificar que el DNI proporcionado coincida con el registrado
        if user.dni != dni:
            # Si el DNI no coincide, rechazar la autenticación
            # Esto previene que alguien con solo el email pueda intentar autenticarse
            return None
        
        # Paso 5: Verificar que la contraseña sea correcta
        if user.check_password(password):
            # Paso 6: Verificaciones adicionales de seguridad
            
            # Verificar que la cuenta esté activa
            if not user.is_active:
                return None
            
            # Aquí podrían agregarse más verificaciones como:
            # - Verificar si la cuenta está bloqueada por intentos fallidos
            # - Verificar si la cuenta ha expirado
            # - Verificar restricciones por horario/IP, etc.
            
            # Paso 7: Autenticación exitosa
            return user
        
        # Paso 8: Si la contraseña es incorrecta
        return None
    
    def get_user(self, user_id):
        """
        Obtiene un usuario por su ID.
        
        Este método es requerido por Django para recuperar usuarios
        de la sesión después de la autenticación inicial.
        
        Args:
            user_id: El ID del usuario a recuperar
            
        Returns:
            User: El usuario si existe y está activo
            None: Si no existe o no está activo
        """
        try:
            user = User.objects.get(pk=user_id)
            return user if user.is_active else None
        except User.DoesNotExist:
            return None
