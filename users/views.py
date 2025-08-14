"""
Vistas para la app users.

Este módulo contiene las vistas para funcionalidades específicas de usuarios,
incluyendo login personalizado y cambio de contraseña obligatorio.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.http import HttpResponseRedirect

from .forms import LoginForm, CustomPasswordChangeForm
from .auth_backends import EmailDNIBackend


@csrf_protect
@never_cache
def login_view(request):
    """
    Vista de login personalizada usando EmailDNIBackend.
    
    Esta vista maneja el proceso de autenticación usando email, DNI y contraseña.
    Utiliza el backend personalizado EmailDNIBackend para mayor seguridad.
    
    Args:
        request: El objeto HttpRequest
        
    Returns:
        HttpResponse: Renderiza el template de login o redirige si es exitoso
    """
    
    # Si el usuario ya está autenticado, redirigir a home
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            # Obtener datos limpios del formulario
            email = form.cleaned_data['email']
            dni = form.cleaned_data['dni']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Intentar autenticación usando el backend personalizado
            user = authenticate(
                request,
                username=email,  # EmailDNIBackend usa 'username' para el email
                password=password,
                dni=dni
            )
            
            if user is not None:
                # Autenticación exitosa
                login(request, user)
                
                # Configurar duración de sesión
                if remember_me:
                    # Mantener sesión por 30 días
                    request.session.set_expiry(30 * 24 * 60 * 60)
                else:
                    # Sesión expira al cerrar el navegador
                    request.session.set_expiry(0)
                
                # Limpiar flag de mensaje de cambio de contraseña
                request.session.pop('password_change_message_shown', None)
                
                # Mensaje de bienvenida
                messages.success(
                    request,
                    f'¡Bienvenido {user.get_full_name()}! Has iniciado sesión correctamente.'
                )
                
                # Redirigir a la página solicitada o a home por defecto
                next_url = request.GET.get('next') or reverse('core:home')
                return HttpResponseRedirect(next_url)
            
            else:
                # Autenticación fallida
                messages.error(
                    request,
                    '❌ Credenciales incorrectas. Verifica tu email, DNI y contraseña.'
                )
                
                # Por seguridad, no especificar qué campo específico está mal
                # Esto previene ataques de enumeración de usuarios
        
        else:
            # Formulario inválido
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
    
    Esta vista se utiliza cuando un usuario tiene must_change_password=True.
    Después del cambio exitoso, actualiza el flag a False y redirige a home.
    
    Args:
        request: El objeto HttpRequest
        
    Returns:
        HttpResponse: Renderiza el template de cambio o redirige si es exitoso
    """
    
    # Verificar si el usuario realmente necesita cambiar la contraseña
    if not request.user.must_change_password:
        messages.info(
            request,
            'Ya has actualizado tu contraseña. No es necesario cambiarla nuevamente.'
        )
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        
        if form.is_valid():
            # Guardar la nueva contraseña
            user = form.save()
            
            # IMPORTANTE: Actualizar el flag must_change_password
            user.must_change_password = False
            user.save(update_fields=['must_change_password'])
            
            # Limpiar flag de mensaje de cambio de contraseña de la sesión
            request.session.pop('password_change_message_shown', None)
            
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
    user_name = request.user.get_full_name()
    logout(request)
    
    messages.success(
        request,
        f'👋 ¡Hasta luego {user_name}! Has cerrado sesión correctamente.'
    )
    
    return redirect('users:login')
