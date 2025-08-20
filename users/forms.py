"""
Formularios personalizados para la app users.

Este módulo contiene formularios específicos para funcionalidades de usuarios,
incluyendo formularios de login, cambio de contraseña, registro y edición de perfil.

Características:
- Validaciones avanzadas de seguridad
- Estilos Bootstrap 5 integrados
- Mensajes de error personalizados
- Validaciones de contraseñas seguras
- Formularios responsive y accesibles
"""

import re
from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()


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
            'class': 'form-control form-control-lg',
            'placeholder': 'tu-email@ejemplo.com',
            'autocomplete': 'email',
            'autofocus': True,
            'aria-describedby': 'emailHelp',
        }),
        help_text='Ingresa tu dirección de correo electrónico registrada.',
        error_messages={
            'required': '📧 El correo electrónico es obligatorio.',
            'invalid': '❌ Ingresa un correo electrónico válido.',
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
            'class': 'form-control form-control-lg',
            'placeholder': 'Nueva contraseña',
            'autocomplete': 'new-password',
            'aria-describedby': 'newPasswordHelp',
        })
        self.fields['new_password1'].help_text = (
            '🔐 Tu contraseña debe tener al menos 8 caracteres, '
            'incluir letras mayúsculas, minúsculas, números y un símbolo especial.'
        )
        
        # Personalizar el campo de confirmación
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirmar nueva contraseña',
            'autocomplete': 'new-password',
            'aria-describedby': 'confirmPasswordHelp',
        })
        self.fields['new_password2'].help_text = '🔄 Repite la nueva contraseña para confirmar.'
        
        # Actualizar etiquetas
        self.fields['old_password'].label = '🔒 Contraseña Actual'
        self.fields['new_password1'].label = '🆕 Nueva Contraseña'
        self.fields['new_password2'].label = '✅ Confirmar Nueva Contraseña'
    
    def clean_new_password1(self):
        """
        Validación avanzada de la nueva contraseña.
        
        Returns:
            str: Nueva contraseña validada
            
        Raises:
            ValidationError: Si la contraseña no cumple los requisitos
        """
        password = self.cleaned_data.get('new_password1')
        
        if password:
            # Verificar longitud mínima
            if len(password) < 8:
                raise ValidationError('🔐 La contraseña debe tener al menos 8 caracteres.')
            
            # Verificar que contenga al menos una letra minúscula
            if not re.search(r'[a-z]', password):
                raise ValidationError('🔤 La contraseña debe contener al menos una letra minúscula.')
            
            # Verificar que contenga al menos una letra mayúscula
            if not re.search(r'[A-Z]', password):
                raise ValidationError('🔠 La contraseña debe contener al menos una letra mayúscula.')
            
            # Verificar que contenga al menos un número
            if not re.search(r'\d', password):
                raise ValidationError('🔢 La contraseña debe contener al menos un número.')
            
            # Verificar que contenga al menos un carácter especial
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError('🔣 La contraseña debe contener al menos un símbolo especial (!@#$%^&*(),.?":{}|<>).')
            
            # Verificar que no sea demasiado común
            common_passwords = [
                'password', '12345678', 'qwerty123', 'admin123', 
                'Password1', 'password123', '123456789', 'admin1234'
            ]
            if password.lower() in [p.lower() for p in common_passwords]:
                raise ValidationError('🚫 Esta contraseña es demasiado común. Elige una más segura.')
        
        return password


class UserRegistrationForm(UserCreationForm):
    """
    Formulario de registro de usuarios con campos adicionales.
    
    Extiende UserCreationForm con campos específicos para el sistema escolar.
    """
    
    email = forms.EmailField(
        label='Correo Electrónico',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com',
            'autocomplete': 'email',
        }),
        help_text='📧 Ingresa un correo electrónico válido.',
    )
    
    dni = forms.CharField(
        label='DNI/Cédula',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345678',
            'autocomplete': 'off',
        }),
        help_text='🆔 Documento Nacional de Identidad.',
    )
    
    first_name = forms.CharField(
        label='Nombres',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Juan Carlos',
            'autocomplete': 'given-name',
        }),
        help_text='👤 Nombres completos.',
    )
    
    last_name = forms.CharField(
        label='Apellidos',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'García López',
            'autocomplete': 'family-name',
        }),
        help_text='👥 Apellidos completos.',
    )
    
    phone = forms.CharField(
        label='Teléfono',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1234567890',
            'autocomplete': 'tel',
        }),
        help_text='📱 Número de teléfono (opcional).',
    )
    
    birth_date = forms.DateField(
        label='Fecha de Nacimiento',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'autocomplete': 'bday',
        }),
        help_text='🎂 Tu fecha de nacimiento (opcional).',
    )
    
    role = forms.ChoiceField(
        label='Rol en el Sistema',
        choices=[
            ('', 'Selecciona un rol'),
            ('student', '👨‍🎓 Estudiante'),
            ('teacher', '👨‍🏫 Profesor'),
            ('parent', '👨‍👩‍👧‍👦 Padre/Madre'),
            ('staff', '👨‍💼 Personal Administrativo'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        help_text='🎭 Selecciona tu rol principal en la institución.',
    )
    
    terms_accepted = forms.BooleanField(
        label='Acepto los términos y condiciones',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        help_text='📋 Debes aceptar los términos para continuar.',
        error_messages={
            'required': '✅ Debes aceptar los términos y condiciones.',
        }
    )
    
    class Meta:
        model = User
        fields = ('email', 'dni', 'first_name', 'last_name', 'phone', 'birth_date', 'role', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar campos de contraseña
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña segura',
            'autocomplete': 'new-password',
        })
        self.fields['password1'].help_text = (
            '🔐 Mínimo 8 caracteres con mayúsculas, minúsculas, números y símbolos.'
        )
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].help_text = '🔄 Repite la contraseña para confirmar.'
        
        # Actualizar etiquetas
        self.fields['password1'].label = '🔒 Contraseña'
        self.fields['password2'].label = '✅ Confirmar Contraseña'
    
    def clean_email(self):
        """Validación del email."""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            if User.objects.filter(email=email).exists():
                raise ValidationError('📧 Ya existe un usuario con este correo electrónico.')
        return email
    
    def clean_dni(self):
        """Validación del DNI."""
        dni = self.cleaned_data.get('dni')
        if dni:
            dni = dni.strip().upper()
            if User.objects.filter(dni=dni).exists():
                raise ValidationError('🆔 Ya existe un usuario con este DNI.')
            if len(dni) < 5:
                raise ValidationError('📏 El DNI debe tener al menos 5 caracteres.')
        return dni
    
    def clean_birth_date(self):
        """Validación de la fecha de nacimiento."""
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = timezone.now().date()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if birth_date >= today:
                raise ValidationError('📅 La fecha de nacimiento no puede ser en el futuro.')
            if age > 120:
                raise ValidationError('📅 Por favor verifica la fecha de nacimiento.')
            if age < 5 and self.cleaned_data.get('role') == 'teacher':
                raise ValidationError('📅 La edad no es apropiada para el rol seleccionado.')
        
        return birth_date


class UserProfileForm(forms.ModelForm):
    """
    Formulario para editar el perfil del usuario.
    
    Permite a los usuarios actualizar su información personal.
    """
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'address', 'birth_date']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa',
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }
        help_texts = {
            'first_name': '👤 Tus nombres completos',
            'last_name': '👥 Tus apellidos completos',
            'phone': '📱 Número de teléfono de contacto',
            'address': '🏠 Tu dirección completa',
            'birth_date': '🎂 Tu fecha de nacimiento',
        }
    
    def clean_birth_date(self):
        """Validación de fecha de nacimiento."""
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = timezone.now().date()
            if birth_date >= today:
                raise ValidationError('📅 La fecha de nacimiento no puede ser en el futuro.')
        return birth_date


class PasswordResetRequestForm(forms.Form):
    """
    Formulario para solicitar restablecimiento de contraseña.
    
    Requiere email y DNI para mayor seguridad.
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
        help_text='📧 Correo electrónico registrado en tu cuenta.',
    )
    
    dni = forms.CharField(
        label='DNI/Cédula',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345678',
            'autocomplete': 'off',
        }),
        help_text='🆔 Tu Documento Nacional de Identidad.',
    )
    
    def clean(self):
        """Validación cruzada de email y DNI."""
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        dni = cleaned_data.get('dni')
        
        if email and dni:
            try:
                user = User.objects.get(email=email.lower(), dni=dni.upper())
                if not user.is_active:
                    raise ValidationError('❌ Esta cuenta no está activa.')
            except User.DoesNotExist:
                raise ValidationError('❌ No se encontró una cuenta con estos datos.')
        
        return cleaned_data
