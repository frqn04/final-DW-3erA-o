"""
Configuración de URLs para la app users.

Este módulo define las rutas URL específicas para funcionalidades de usuarios.
"""

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # ================================
    # AUTENTICACIÓN
    # ================================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Cambio de contraseña obligatorio
    path('change-password-first-login/', 
         views.change_password_first_login, 
         name='change_password_first_login'),
    
    # ================================
    # GESTIÓN DE PERFIL
    # ================================
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('activity/', views.UserActivityLogView.as_view(), name='activity_log'),
    
    # ================================
    # REGISTRO (solo si está habilitado en settings)
    # ================================
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    
    # ================================
    # RESET DE CONTRASEÑA
    # ================================
    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    
    # ================================
    # ADMINISTRACIÓN (solo para staff)
    # ================================
    path('admin/users/', views.admin_user_list_view, name='admin_user_list'),
    path('admin/users/<int:user_id>/toggle-status/', 
         views.admin_toggle_user_status, 
         name='admin_toggle_user_status'),
]
