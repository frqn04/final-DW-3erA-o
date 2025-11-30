from django import forms
from django.contrib.auth import get_user_model
from .models import Alumno

User = get_user_model()


class AlumnoForm(forms.ModelForm):
    """Formulario para crear/editar alumnos"""
    
    crear_usuario = forms.BooleanField(
        required=False,
        initial=True,
        label='Crear usuario automáticamente',
        help_text='Se creará un usuario con email {DNI}@universidad.edu y contraseña igual al DNI'
    )
    
    class Meta:
        model = Alumno
        fields = ['first_name', 'last_name', 'dni', 'carrera', 'fecha_ingreso', 'activo', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'dni': 'Debe contener exactamente 8 dígitos numéricos',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando un alumno existente que ya tiene usuario, ocultar la opción
        if self.instance.pk and self.instance.user:
            self.fields['crear_usuario'].widget = forms.HiddenInput()
            self.fields['crear_usuario'].initial = False
        
        # Agregar atributos HTML5 para mejor validación
        self.fields['dni'].widget.attrs.update({
            'pattern': r'\d{8}',
            'maxlength': '8',
            'minlength': '8',
            'placeholder': '12345678',
            'title': 'Ingrese exactamente 8 dígitos numéricos'
        })
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'Ingrese el nombre'
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Ingrese el apellido'
        })
    
    def clean_dni(self):
        """Validar que el DNI tenga el formato correcto"""
        dni = self.cleaned_data.get('dni')
        
        if not dni:
            raise forms.ValidationError('⚠️ El DNI es obligatorio.')
        
        if not dni.isdigit():
            raise forms.ValidationError('⚠️ El DNI debe contener solo números (sin puntos, guiones ni espacios).')
        
        if len(dni) < 8:
            raise forms.ValidationError(f'⚠️ El DNI debe tener exactamente 8 dígitos. Ingresaste {len(dni)} dígito(s).')
        
        if len(dni) > 8:
            raise forms.ValidationError(f'⚠️ El DNI debe tener exactamente 8 dígitos. Ingresaste {len(dni)} dígito(s).')
        
        return dni
    
    def save(self, commit=True):
        """Crear usuario automáticamente si se seleccionó la opción"""
        alumno = super().save(commit=False)
        
        # Solo crear usuario si es un alumno nuevo y se marcó la opción
        if not alumno.pk and self.cleaned_data.get('crear_usuario'):
            dni = self.cleaned_data.get('dni')
            email = f"{dni}@universidad.edu"
            
            # Verificar si ya existe un usuario con ese email o DNI
            if not User.objects.filter(email=email).exists() and not User.objects.filter(dni=dni).exists():
                # Crear el usuario
                user = User.objects.create_user(
                    email=email,
                    dni=dni,
                    password=dni,  # Contraseña igual al DNI
                    first_name=self.cleaned_data.get('first_name'),
                    last_name=self.cleaned_data.get('last_name'),
                    role='ALUMNO',
                    must_change_password=True  # Forzar cambio de contraseña en primer login
                )
                alumno.user = user
                
                # Actualizar el email del alumno para que coincida
                alumno.email = email
        
        if commit:
            alumno.save()
        
        return alumno
