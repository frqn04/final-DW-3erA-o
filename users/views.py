"""
Vistas para la app users.

Este módulo contiene las vistas para funcionalidades específicas de usuarios,
incluyendo login personalizado, cambio de contraseña y gestión de perfil.

Características:
- Autenticación multi-factor con email + DNI
- Logging de seguridad detallado
- Protección contra ataques comunes
- Gestión de sesiones segura
"""

import logging
import time
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.views.generic import CreateView, UpdateView, ListView
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import LoginForm, CustomPasswordChangeForm

User = get_user_model()
logger = logging.getLogger('users.views')


def _get_client_ip(request):
    """Obtiene la IP real del cliente considerando proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def _is_safe_url(url, request):
    """
    Verifica si una URL es segura para redirección.
    
    Args:
        url: URL a verificar
        request: HttpRequest object
        
    Returns:
        bool: True si la URL es segura
    """
    if not url:
        return False
    
    # URL debe ser relativa o del mismo dominio
    if url.startswith('/'):
        return True
    
    # Verificar dominio si es URL absoluta
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc == request.get_host()
    except:
        return False


@csrf_protect
@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Vista de login personalizada con autenticación multi-factor.
    
    Esta vista maneja el proceso de autenticación usando email, DNI y contraseña.
    Utiliza el backend personalizado configurado en settings para mayor seguridad.
    
    Features:
    - Autenticación multi-factor (email + DNI + password)
    - Logging de intentos de login
    - Protección contra ataques de fuerza bruta
    - Gestión de sesiones con "recordarme"
    - Redirección inteligente post-login
    
    Args:
        request: El objeto HttpRequest
        
    Returns:
        HttpResponse: Renderiza el template de login o redirige si es exitoso
    """
    
    # Si el usuario ya está autenticado, redirigir
    if request.user.is_authenticated:
        next_url = request.GET.get('next', reverse('core:home'))
        return redirect(next_url)
    
    # Obtener IP del cliente para logging
    client_ip = _get_client_ip(request)
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            # Obtener datos limpios del formulario
            email = form.cleaned_data['email']
            dni = form.cleaned_data['dni']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Log del intento de login
            logger.info(f"Login attempt for email: {email} from IP: {client_ip}")
            
            # Intentar autenticación con el backend personalizado
            user = authenticate(
                request, 
                username=email, 
                password=password, 
                dni=dni
            )
            
            if user is not None:
                # Autenticación exitosa
                login(request, user)
                
                # Configurar duración de sesión según "recordarme"
                if remember_me:
                    # Sesión de 30 días
                    request.session.set_expiry(30 * 24 * 60 * 60)
                    logger.info(f"Extended session set for user: {user.email}")
                else:
                    # Sesión hasta cerrar navegador
                    request.session.set_expiry(0)
                
                # Mensaje de bienvenida
                messages.success(
                    request,
                    f'🎉 ¡Bienvenido/a {user.get_full_name() or user.email}! '
                    f'Has iniciado sesión correctamente.'
                )
                
                # Determinar URL de redirección
                next_url = request.GET.get('next')
                if next_url and _is_safe_url(next_url, request):
                    redirect_url = next_url
                else:
                    redirect_url = reverse('core:home')
                
                logger.info(f"Successful login for user: {user.email}, redirecting to: {redirect_url}")
                
                return redirect(redirect_url)
            
            else:
                # Autenticación fallida
                logger.warning(f"Failed login attempt for email: {email} from IP: {client_ip}")
                
                messages.error(
                    request,
                    '❌ Credenciales inválidas. Verifica tu email, DNI y contraseña. '
                    'Si el problema persiste, contacta al administrador.'
                )
                
                # Agregar delay para mitigar ataques de fuerza bruta
                time.sleep(1)
        
        else:
            # Formulario inválido
            logger.warning(f"Invalid login form submission from IP: {client_ip}")
            
            messages.error(
                request,
                '❌ Por favor corrige los errores en el formulario.'
            )
    
    else:
        # Petición GET - mostrar formulario vacío
        form = LoginForm()
    
    context = {
        'form': form,
        'title': 'Iniciar Sesión - Sistema Escolar',
    }
    
    return render(request, 'users/login.html', context)


@login_required
@csrf_protect
def change_password_first_login(request):
    """
    Vista para cambio obligatorio de contraseña en el primer login.
    
    Esta vista se utiliza cuando un usuario tiene password_change_required=True.
    El middleware ForcePasswordChangeMiddleware redirige automáticamente aquí.
    
    Process:
    1. Verificar que el usuario realmente necesite cambiar contraseña
    2. Procesar formulario de cambio de contraseña
    3. Actualizar flag y redirigir al home
    
    Args:
        request: El objeto HttpRequest
        
    Returns:
        HttpResponse: Renderiza el template o redirige si es exitoso
    """
    
    # Verificar que el usuario realmente necesite cambiar contraseña
    password_change_required = False
    
    # Verificar diferentes nombres de atributos para compatibilidad
    if hasattr(request.user, 'password_change_required'):
        password_change_required = request.user.password_change_required
    elif hasattr(request.user, 'must_change_password'):
        password_change_required = request.user.must_change_password
    
    if not password_change_required:
        # Si no necesita cambiar contraseña, redirigir a home
        messages.info(
            request,
            'ℹ️ No necesitas cambiar tu contraseña en este momento.'
        )
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        
        if form.is_valid():
            # Guardar la nueva contraseña
            user = form.save()
            
            # Marcar que ya no necesita cambiar contraseña
            if hasattr(user, 'password_change_required'):
                user.password_change_required = False
            elif hasattr(user, 'must_change_password'):
                user.must_change_password = False
            
            if hasattr(user, 'password_changed_at'):
                user.password_changed_at = timezone.now()
            
            # Guardar solo los campos que existen
            fields_to_update = []
            if hasattr(user, 'password_change_required'):
                fields_to_update.append('password_change_required')
            elif hasattr(user, 'must_change_password'):
                fields_to_update.append('must_change_password')
            if hasattr(user, 'password_changed_at'):
                fields_to_update.append('password_changed_at')
            
            if fields_to_update:
                user.save(update_fields=fields_to_update)
            
            # Log de cambio exitoso
            logger.info(f"Password successfully changed for user: {user.email}")
            
            # Crear log de actividad si el modelo existe
            try:
                from .models import UserActivityLog
                UserActivityLog.objects.create(
                    user=user,
                    action='password_change_success',
                    details='Password changed during first login',
                    ip_address=_get_client_ip(request)
                )
            except Exception as e:
                logger.error(f"Error creating activity log: {e}")
            
            # Limpiar flag de mensaje mostrado
            if 'password_change_message_shown' in request.session:
                del request.session['password_change_message_shown']
            
            # Mensaje de éxito
            messages.success(
                request,
                '✅ ¡Contraseña actualizada exitosamente! '
                'Ahora puedes acceder a todas las funcionalidades del sistema.'
            )
            
            # Redirigir a home
            return redirect('core:home')
        
        else:
            # Formulario inválido - mostrar errores
            messages.error(
                request,
                '❌ Hubo errores al cambiar tu contraseña. '
                'Por favor revisa los campos marcados.'
            )
    
    else:
        # Petición GET - mostrar formulario vacío
        form = CustomPasswordChangeForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Cambiar Contraseña - Primer Acceso',
        'user': request.user,
    }
    
    return render(request, 'users/change_password_first_login.html', context)


@login_required
def logout_view(request):
    """
    Vista para cerrar sesión.
    
    Args:
        request: El objeto HttpRequest
        
    Returns:
        HttpResponse: Redirige al login con mensaje de confirmación
    """
    user_name = request.user.get_full_name() or request.user.email
    user_email = request.user.email
    
    # Log de logout
    logger.info(f"User logout: {user_email}")
    
    # Crear log de actividad antes del logout si el modelo existe
    try:
        from .models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='logout',
            details='User logged out',
            ip_address=_get_client_ip(request)
        )
    except Exception as e:
        logger.error(f"Error creating logout activity log: {e}")
    
    logout(request)
    
    messages.success(
        request,
        f'👋 ¡Hasta luego {user_name}! Has cerrado sesión correctamente.'
    )
    
    return redirect('users:login')


# ================================
# VISTAS BASADAS EN CLASES
# ================================

class UserRegistrationView(CreateView):
    """
    Vista para registro de nuevos usuarios.
    
    Solo disponible si ALLOW_USER_REGISTRATION está habilitado.
    """
    model = User
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    fields = ['first_name', 'last_name', 'email', 'dni', 'phone', 'birth_date']
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar si el registro está habilitado."""
        if not getattr(settings, 'ALLOW_USER_REGISTRATION', False):
            messages.error(request, '❌ El registro de usuarios no está habilitado.')
            return redirect('users:login')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Procesar registro exitoso."""
        # Configurar usuario como inactivo por defecto
        user = form.save(commit=False)
        user.is_active = False
        user.password_change_required = True
        user.set_password('temporal123')  # Contraseña temporal
        user.save()
        
        # Log de registro
        logger.info(f"New user registered: {user.email}")
        
        # Crear log de actividad
        try:
            from .models import UserActivityLog
            UserActivityLog.objects.create(
                user=user,
                action='user_registration',
                details='New user registered',
                ip_address=_get_client_ip(self.request)
            )
        except Exception as e:
            logger.error(f"Error creating registration log: {e}")
        
        messages.success(
            self.request,
            '✅ ¡Registro exitoso! Tu cuenta ha sido creada pero necesita '
            'ser activada por un administrador. Se te enviará un correo con las credenciales.'
        )
        
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Registro de Usuario - Sistema Escolar'
        return context


class UserProfileView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar perfil de usuario.
    """
    model = User
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')
    fields = ['first_name', 'last_name', 'phone', 'address', 'birth_date']
    
    def get_object(self):
        """Retornar el usuario actual."""
        return self.request.user
    
    def form_valid(self, form):
        """Procesar actualización exitosa."""
        response = super().form_valid(form)
        
        # Log de actualización
        logger.info(f"User profile updated: {self.request.user.email}")
        
        # Crear log de actividad
        try:
            from .models import UserActivityLog
            UserActivityLog.objects.create(
                user=self.request.user,
                action='profile_update',
                details='User updated profile information',
                ip_address=_get_client_ip(self.request)
            )
        except Exception as e:
            logger.error(f"Error creating profile update log: {e}")
        
        messages.success(
            self.request,
            '✅ ¡Perfil actualizado exitosamente!'
        )
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mi Perfil - Sistema Escolar'
        return context


class UserActivityLogView(LoginRequiredMixin, ListView):
    """
    Vista para mostrar el historial de actividades del usuario.
    """
    template_name = 'users/activity_log.html'
    context_object_name = 'activities'
    paginate_by = 25
    
    def get_queryset(self):
        """Filtrar actividades del usuario actual."""
        try:
            from .models import UserActivityLog
            return UserActivityLog.objects.filter(
                user=self.request.user
            ).order_by('-timestamp')
        except:
            # Si el modelo no existe, retornar queryset vacío
            return User.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mi Actividad - Sistema Escolar'
        return context


# ================================
# VISTAS DE RESET DE CONTRASEÑA
# ================================

@csrf_protect
@never_cache
def password_reset_request_view(request):
    """
    Vista para solicitar restablecimiento de contraseña.
    
    Requiere email y DNI para mayor seguridad.
    """
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        dni = request.POST.get('dni', '').strip().upper()
        
        if not email or not dni:
            messages.error(
                request,
                '❌ Debes proporcionar tanto el email como el DNI.'
            )
        else:
            try:
                user = User.objects.get(email=email, dni=dni)
                
                # Log de solicitud
                logger.info(f"Password reset requested for user: {user.email}")
                
                # Crear log de actividad
                try:
                    from .models import UserActivityLog
                    UserActivityLog.objects.create(
                        user=user,
                        action='password_reset_request',
                        details='Password reset requested',
                        ip_address=_get_client_ip(request)
                    )
                except Exception as e:
                    logger.error(f"Error creating reset request log: {e}")
                
                # Aquí se implementaría el envío de email
                # Por ahora solo mostramos mensaje
                
                messages.success(
                    request,
                    '📧 Si los datos son correctos, recibirás un correo con '
                    'instrucciones para restablecer tu contraseña.'
                )
                
                return redirect('users:login')
                
            except User.DoesNotExist:
                # No revelar si el usuario existe o no
                messages.success(
                    request,
                    '📧 Si los datos son correctos, recibirás un correo con '
                    'instrucciones para restablecer tu contraseña.'
                )
                return redirect('users:login')
    
    context = {
        'title': 'Restablecer Contraseña - Sistema Escolar',
    }
    
    return render(request, 'users/password_reset_request.html', context)


# ================================
# VISTAS DE ADMINISTRACIÓN
# ================================

@staff_member_required
def admin_user_list_view(request):
    """
    Vista para que los administradores vean la lista de usuarios.
    """
    users = User.objects.all().order_by('-date_joined')
    
    # Aplicar filtros de búsqueda
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(dni__icontains=search_query)
        )
    
    # Filtro por estado
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Paginación
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'title': 'Gestión de Usuarios - Sistema Escolar',
    }
    
    return render(request, 'users/admin_user_list.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_toggle_user_status(request, user_id):
    """
    Vista para que los administradores activen/desactiven usuarios.
    """
    user = get_object_or_404(User, id=user_id)
    
    # No permitir desactivar superusuarios
    if user.is_superuser and not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'message': '❌ No tienes permisos para modificar este usuario.'
        })
    
    # Cambiar estado
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    
    # Log de la acción
    action = 'activated' if user.is_active else 'deactivated'
    logger.info(f"User {user.email} {action} by admin {request.user.email}")
    
    # Crear log de actividad
    try:
        from .models import UserActivityLog
        UserActivityLog.objects.create(
            user=user,
            action=f'account_{action}',
            details=f'Account {action} by admin {request.user.email}',
            ip_address=_get_client_ip(request)
        )
    except Exception as e:
        logger.error(f"Error creating admin action log: {e}")
    
    return JsonResponse({
        'success': True,
        'message': f'✅ Usuario {"activado" if user.is_active else "desactivado"} correctamente.',
        'is_active': user.is_active
    })
