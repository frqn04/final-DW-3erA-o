"""
Backends de autenticación personalizados para la app users.

Este módulo contiene backends de autenticación alternativos que permiten
diferentes métodos de autenticación además del método estándar de Django.

Incluye características avanzadas de seguridad como:
- Autenticación multi-factor (email + DNI + password)
- Protección contra ataques de timing
- Sistema de bloqueo por intentos fallidos
- Logging de seguridad detallado
- Verificaciones adicionales de estado de cuenta
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

User = get_user_model()
logger = logging.getLogger('users.auth')


class EmailDNIBackend(ModelBackend):
    """
    Backend de autenticación que requiere email, DNI y contraseña.
    
    Este backend personalizado permite autenticación más segura requiriendo
    que el usuario proporcione tanto su email como su DNI registrado,
    además de la contraseña. Esto añade una capa extra de seguridad.
    
    Características de seguridad:
    - Multi-factor authentication (email + DNI + password)
    - Protección contra timing attacks
    - Sistema de bloqueo por intentos fallidos
    - Logging detallado de eventos de seguridad
    - Verificaciones de estado de cuenta
    """
    
    # Configuración de seguridad
    MAX_LOGIN_ATTEMPTS = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
    LOCKOUT_DURATION = getattr(settings, 'LOCKOUT_DURATION_MINUTES', 30)  # minutos
    TIMING_ATTACK_DELAY = 0.5  # segundos para simular procesamiento
    
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
        
        # Obtener IP del cliente para logging
        client_ip = self._get_client_ip(request)
        
        # Paso 1: Validar que se proporcionen todos los datos requeridos
        if not username or not password or not dni:
            logger.warning(
                f"Login attempt with incomplete credentials from IP {client_ip}. "
                f"Missing: {[field for field, val in [('email', username), ('password', password), ('dni', dni)] if not val]}"
            )
            # Simular tiempo de procesamiento para evitar timing attacks
            time.sleep(self.TIMING_ATTACK_DELAY)
            return None
        
        # Normalizar email
        email = username.lower().strip()
        
        # Paso 2: Verificar si la IP está bloqueada
        if self._is_ip_blocked(client_ip):
            logger.warning(f"Login attempt from blocked IP: {client_ip}")
            return None
        
        try:
            # Paso 3: Buscar el usuario por email
            user = User.objects.get(email__iexact=email)
            
        except User.DoesNotExist:
            # Paso 4a: Si el email no existe en la base de datos
            logger.info(f"Login attempt with non-existent email: {email} from IP: {client_ip}")
            
            # Ejecutamos check_password para evitar timing attacks
            User().check_password(password)
            
            # Registrar intento fallido por IP
            self._record_failed_attempt(client_ip, 'non_existent_email')
            
            # Simular tiempo adicional de procesamiento
            time.sleep(self.TIMING_ATTACK_DELAY)
            return None
            
        except User.MultipleObjectsReturned:
            # Paso 4b: Error de integridad - múltiples usuarios con mismo email
            logger.error(f"Multiple users found with email: {email}")
            return None
        
        # Paso 5: Verificar si el usuario está bloqueado
        if self._is_user_blocked(user):
            logger.warning(f"Login attempt for blocked user: {user.email} from IP: {client_ip}")
            return None
        
        # Paso 6: Verificar que el DNI proporcionado coincida
        if user.dni != dni:
            logger.warning(
                f"Login attempt with incorrect DNI for user: {user.email} from IP: {client_ip}"
            )
            self._record_failed_attempt(client_ip, 'incorrect_dni', user)
            return None
        
        # Paso 7: Verificar que la contraseña sea correcta
        if not user.check_password(password):
            logger.warning(
                f"Login attempt with incorrect password for user: {user.email} from IP: {client_ip}"
            )
            self._record_failed_attempt(client_ip, 'incorrect_password', user)
            return None
        
        # Paso 8: Verificaciones adicionales de seguridad
        security_check = self._perform_security_checks(user, client_ip)
        if not security_check['allowed']:
            logger.warning(
                f"Login denied for user: {user.email} from IP: {client_ip}. "
                f"Reason: {security_check['reason']}"
            )
            return None
        
        # Paso 9: Autenticación exitosa
        self._record_successful_login(user, client_ip)
        
        logger.info(f"Successful login for user: {user.email} from IP: {client_ip}")
        
        return user
    
    def _get_client_ip(self, request):
        """Obtiene la IP real del cliente considerando proxies."""
        if not request:
            return 'unknown'
            
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _is_ip_blocked(self, ip):
        """Verifica si una IP está bloqueada por intentos fallidos."""
        if ip == 'unknown':
            return False
            
        cache_key = f'blocked_ip_{ip}'
        return cache.get(cache_key, False)
    
    def _is_user_blocked(self, user):
        """Verifica si un usuario está bloqueado por intentos fallidos."""
        cache_key = f'blocked_user_{user.id}'
        return cache.get(cache_key, False)
    
    def _record_failed_attempt(self, ip, reason, user=None):
        """Registra un intento fallido y aplica bloqueos si es necesario."""
        # Incrementar contador de intentos fallidos por IP
        ip_attempts_key = f'failed_attempts_ip_{ip}'
        ip_attempts = cache.get(ip_attempts_key, 0) + 1
        cache.set(ip_attempts_key, ip_attempts, timeout=self.LOCKOUT_DURATION * 60)
        
        # Si se alcanza el límite, bloquear IP
        if ip_attempts >= self.MAX_LOGIN_ATTEMPTS:
            cache.set(f'blocked_ip_{ip}', True, timeout=self.LOCKOUT_DURATION * 60)
            logger.warning(f"IP {ip} blocked for {self.LOCKOUT_DURATION} minutes after {ip_attempts} failed attempts")
        
        # Si hay un usuario específico, registrar intentos para ese usuario
        if user:
            user_attempts_key = f'failed_attempts_user_{user.id}'
            user_attempts = cache.get(user_attempts_key, 0) + 1
            cache.set(user_attempts_key, user_attempts, timeout=self.LOCKOUT_DURATION * 60)
            
            # Si se alcanza el límite, bloquear usuario
            if user_attempts >= self.MAX_LOGIN_ATTEMPTS:
                cache.set(f'blocked_user_{user.id}', True, timeout=self.LOCKOUT_DURATION * 60)
                logger.warning(f"User {user.email} blocked for {self.LOCKOUT_DURATION} minutes after {user_attempts} failed attempts")
                
                # Actualizar campos de seguridad en el modelo
                user.failed_login_attempts = user_attempts
                user.last_failed_login = timezone.now()
                if user_attempts >= self.MAX_LOGIN_ATTEMPTS:
                    user.account_locked_until = timezone.now() + timedelta(minutes=self.LOCKOUT_DURATION)
                user.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])
    
    def _record_successful_login(self, user, ip):
        """Registra un login exitoso y limpia contadores de intentos fallidos."""
        # Limpiar contadores de intentos fallidos
        cache.delete(f'failed_attempts_ip_{ip}')
        cache.delete(f'failed_attempts_user_{user.id}')
        cache.delete(f'blocked_ip_{ip}')
        cache.delete(f'blocked_user_{user.id}')
        
        # Actualizar campos de último login en el modelo
        now = timezone.now()
        user.last_login_ip = ip
        user.last_successful_login = now
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.save(update_fields=[
            'last_login_ip', 'last_successful_login', 
            'failed_login_attempts', 'account_locked_until'
        ])
        
        # Registrar actividad en el log de actividades
        try:
            from .models import UserActivityLog
            UserActivityLog.objects.create(
                user=user,
                action='login_success',
                details=f'Successful login from IP: {ip}',
                ip_address=ip
            )
        except Exception as e:
            logger.error(f"Error creating activity log for user {user.email}: {e}")
    
    def _perform_security_checks(self, user, ip):
        """Realiza verificaciones adicionales de seguridad."""
        
        # Verificar que la cuenta esté activa
        if not user.is_active:
            return {'allowed': False, 'reason': 'account_inactive'}
        
        # Verificar estado de la cuenta
        if hasattr(user, 'status') and user.status != User.UserStatus.ACTIVE:
            return {'allowed': False, 'reason': f'account_status_{user.status}'}
        
        # Verificar si la cuenta está bloqueada por tiempo
        if hasattr(user, 'account_locked_until') and user.account_locked_until:
            if timezone.now() < user.account_locked_until:
                return {'allowed': False, 'reason': 'account_locked'}
        
        # Verificar si se requiere cambio de contraseña
        if hasattr(user, 'password_change_required') and user.password_change_required:
            # Permitir login pero marcar que necesita cambio de contraseña
            pass
        
        # Aquí se pueden agregar más verificaciones como:
        # - Restricciones por horario
        # - Verificación de ubicación/IP permitidas
        # - Verificación de dispositivos conocidos
        # - etc.
        
        return {'allowed': True, 'reason': 'all_checks_passed'}
    
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
            
            # Verificaciones adicionales para sesiones existentes
            if not user.is_active:
                return None
                
            # Verificar si la cuenta está bloqueada
            if hasattr(user, 'account_locked_until') and user.account_locked_until:
                if timezone.now() < user.account_locked_until:
                    return None
            
            # Verificar estado de la cuenta
            if hasattr(user, 'status') and user.status not in [User.UserStatus.ACTIVE]:
                return None
                
            return user
            
        except User.DoesNotExist:
            return None


class SimpleEmailBackend(ModelBackend):
    """
    Backend de autenticación simple que solo requiere email y contraseña.
    
    Este backend es útil para casos donde no se requiere el DNI,
    como login de administradores o en desarrollo.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica a un usuario usando solo email y contraseña.
        
        Args:
            request: La petición HTTP actual
            username: El email del usuario
            password: La contraseña del usuario
            **kwargs: Argumentos adicionales
            
        Returns:
            User: El usuario autenticado si las credenciales son válidas
            None: Si las credenciales son inválidas
        """
        if username is None or password is None:
            return None
        
        email = username.lower().strip()
        
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Protección contra timing attacks
            User().check_password(password)
            return None
        except User.MultipleObjectsReturned:
            return None
        
        if user.check_password(password) and user.is_active:
            return user
        
        return None


class AdminBackend(ModelBackend):
    """
    Backend de autenticación especial para staff y superusers.
    
    Permite autenticación con email/username y password,
    pero solo para usuarios con permisos de staff.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica a usuarios staff usando email/username y contraseña.
        
        Args:
            request: La petición HTTP actual
            username: El email o username del usuario
            password: La contraseña del usuario
            **kwargs: Argumentos adicionales
            
        Returns:
            User: El usuario autenticado si es staff y las credenciales son válidas
            None: Si no es staff o las credenciales son inválidas
        """
        if username is None or password is None:
            return None
        
        # Intentar autenticación por email primero
        try:
            user = User.objects.get(email__iexact=username.lower())
        except User.DoesNotExist:
            # Si no se encuentra por email, intentar por username si existe
            try:
                user = User.objects.get(username=username)
            except (User.DoesNotExist, AttributeError):
                # Protección contra timing attacks
                User().check_password(password)
                return None
        except User.MultipleObjectsReturned:
            return None
        
        # Verificar que sea staff o superuser
        if not (user.is_staff or user.is_superuser):
            return None
        
        if user.check_password(password) and user.is_active:
            return user
        
        return None
