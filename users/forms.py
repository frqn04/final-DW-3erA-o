"""
Formularios personalizados para la app users.

Este módulo contiene formularios específicos para funcionalidades de usuarios,
incluyendo formularios de login y cambio de contraseña.
"""

from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
import re


class LoginForm(forms.Form):
    """
    Formulario de login personalizado que requiere email, DNI y contraseña.
    
    Este formulario se utiliza junto con el EmailDNIBackend para proporcionar
    autenticación de doble factor usando email y DNI como identificadores.
    """
    
    email = forms.EmailField(
        label='Correo Electrónico',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu-email@ejemplo.com',
            'autocomplete': 'email',
            'autofocus': True,
        }),
        help_text='Ingresa tu dirección de correo electrónico registrada.',
        error_messages={
            'required': 'El correo electrónico es obligatorio.',
            'invalid': 'Ingresa un correo electrónico válido.',
        }
    )
    
    dni = forms.CharField(
        label='DNI/Cédula',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345678',
            'autocomplete': 'off',
        }),
        help_text='Ingresa tu Documento Nacional de Identidad.',
        error_messages={
            'required': 'El DNI es obligatorio.',
            'max_length': 'El DNI no puede tener más de 20 caracteres.',
        }
    )
    
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        }),
        help_text='Ingresa tu contraseña.',
        error_messages={
            'required': 'La contraseña es obligatoria.',
        }
    )
    
    remember_me = forms.BooleanField(
        label='Recordarme',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        help_text='Mantener la sesión iniciada en este dispositivo.',
    )
    
    def clean_email(self):
        """
        Validación personalizada para el campo email.
        
        Returns:
            str: Email normalizado en minúsculas
            
        Raises:
            ValidationError: Si el email no es válido
        """
        email = self.cleaned_data.get('email')
        if email:
            # Normalizar a minúsculas
            email = email.lower().strip()
            
            # Validación adicional de formato (más estricta que la por defecto)
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                raise ValidationError('El formato del correo electrónico no es válido.')
        
        return email
    
    def clean_dni(self):
        """
        Validación personalizada para el campo DNI.
        
        Returns:
            str: DNI limpio sin espacios adicionales
            
        Raises:
            ValidationError: Si el DNI no es válido
        """
        dni = self.cleaned_data.get('dni')
        if dni:
            # Limpiar espacios
            dni = dni.strip()
            
            # Verificar que no esté vacío después de limpiar
            if not dni:
                raise ValidationError('El DNI no puede estar vacío.')
            
            # Verificar que contenga solo números y letras (sin espacios internos)
            if not re.match(r'^[a-zA-Z0-9]+$', dni):
                raise ValidationError('El DNI debe contener solo números y letras, sin espacios.')
            
            # Verificar longitud mínima
            if len(dni) < 5:
                raise ValidationError('El DNI debe tener al menos 5 caracteres.')
        
        return dni
    
    def clean_password(self):
        """
        Validación personalizada para el campo password.
        
        Returns:
            str: Password sin modificaciones
            
        Raises:
            ValidationError: Si la contraseña no cumple requisitos mínimos
        """
        password = self.cleaned_data.get('password')
        if password:
            # Verificar longitud mínima
            if len(password) < 4:  # Mínimo relajado para login
                raise ValidationError('La contraseña debe tener al menos 4 caracteres.')
        
        return password
    
    def clean(self):
        """
        Validación a nivel de formulario.
        
        Returns:
            dict: Datos limpios del formulario
            
        Raises:
            ValidationError: Si hay errores de validación cruzada
        """
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        dni = cleaned_data.get('dni')
        password = cleaned_data.get('password')
        
        # Verificar que todos los campos requeridos estén presentes
        if not email or not dni or not password:
            raise ValidationError(
                'Todos los campos (email, DNI y contraseña) son obligatorios para el login.'
            )
        
        return cleaned_data


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Formulario personalizado para cambio de contraseña en el primer login.
    
    Extiende el PasswordChangeForm de Django con estilos personalizados
    y validaciones adicionales para el contexto escolar.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar el campo de contraseña actual
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña actual',
            'autocomplete': 'current-password',
        })
        self.fields['old_password'].help_text = 'Ingresa tu contraseña temporal actual.'
        
        # Personalizar el campo de nueva contraseña
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nueva contraseña',
            'autocomplete': 'new-password',
        })
        self.fields['new_password1'].help_text = (
            'Tu contraseña debe tener al menos 8 caracteres, '
            'incluir letras y números, y no ser muy común.'
        )
        
        # Personalizar el campo de confirmación
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña',
            'autocomplete': 'new-password',
        })
        self.fields['new_password2'].help_text = 'Repite la nueva contraseña para confirmar.'
        
        # Actualizar etiquetas
        self.fields['old_password'].label = 'Contraseña Actual'
        self.fields['new_password1'].label = 'Nueva Contraseña'
        self.fields['new_password2'].label = 'Confirmar Nueva Contraseña'
