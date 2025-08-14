"""
Configuración de URLs para la app users.

Este módulo define las rutas URL específicas para funcionalidades de usuarios.
"""

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Cambio de contraseña obligatorio
    path('change-password-first-login/', 
         views.change_password_first_login, 
         name='change_password_first_login'),
]
