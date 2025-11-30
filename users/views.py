from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView
from django.contrib.auth.forms import PasswordChangeForm
from .models import User


class LoginView(AuthLoginView):
    """
    Vista de inicio de sesión.
    Soporta autenticación con email o DNI.
    """
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirigir según el rol del usuario"""
        if self.request.user.must_change_password:
            messages.warning(self.request, 'Debes cambiar tu contraseña antes de continuar.')
            return reverse_lazy('users:change_password')
        return reverse_lazy('core:home')


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Vista del perfil del usuario.
    """
    template_name = 'users/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class ChangePasswordView(LoginRequiredMixin, FormView):
    """
    Vista para cambiar contraseña.
    """
    template_name = 'users/change_password.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('core:home')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.save()
        # Actualizar el flag de cambio de contraseña
        user = self.request.user
        user.must_change_password = False
        user.save()
        
        # Re-autenticar al usuario
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(self.request, form.user)
        
        messages.success(self.request, 'Contraseña cambiada exitosamente.')
        return super().form_valid(form)
