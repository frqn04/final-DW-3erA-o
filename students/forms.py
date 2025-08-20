"""
Formularios personalizados para la app students.

Formularios con validaciones avanzadas, widgets personalizados y JavaScript
para mejorar la experiencia del usuario en la gestión de alumnos.

Características implementadas:
- Validación en tiempo real de DNI y email
- Auto-generación de legajo
- Filtrado dinámico de carreras activas
- Widgets de fecha optimizados
- Validaciones cross-field
- JavaScript para UX mejorada
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
import re

from .models import Alumno
from escuelas.models import Carrera


class AlumnoForm(forms.ModelForm):
    """
    Formulario principal para crear y editar alumnos.
    
    Características:
    - Validaciones personalizadas de DNI y email únicos
    - Widget de fecha con calendario
    - Filtrado de carreras activas
    - Auto-generación de legajo opcional
    - Validaciones cross-field
    - JavaScript integrado para UX
    """
    
    class Meta:
        model = Alumno
        fields = [
            'first_name', 'last_name', 'dni', 'email',
            'carrera', 'fecha_ingreso', 'activo', 'observaciones'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre',
                'maxlength': 50,
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ingrese el apellido',
                'maxlength': 50,
            }),
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345678',
                'maxlength': 8,
                'pattern': r'\d{7,8}',
                'title': 'DNI debe tener entre 7 y 8 dígitos',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'estudiante@ejemplo.com',
            }),
            'carrera': forms.Select(attrs={
                'class': 'form-select',
            }),
            'fecha_ingreso': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': timezone.now().date().isoformat(),
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales sobre el alumno...',
                'maxlength': 500,
            }),
        }
        
        labels = {
            'first_name': 'Nombre(s)',
            'last_name': 'Apellido(s)',
            'dni': 'DNI',
            'email': 'Correo Electrónico',
            'carrera': 'Carrera',
            'fecha_ingreso': 'Fecha de Ingreso',
            'activo': 'Alumno Activo',
            'observaciones': 'Observaciones',
        }
        
        help_texts = {
            'first_name': 'Solo letras, espacios y acentos',
            'last_name': 'Solo letras, espacios y acentos',
            'dni': 'Documento Nacional de Identidad (7-8 dígitos)',
            'email': 'Correo electrónico válido y único',
            'carrera': 'Carrera en la que se inscribe el alumno',
            'fecha_ingreso': 'Fecha de ingreso a la institución',
            'activo': 'Indica si el alumno está cursando actualmente',
            'observaciones': 'Notas adicionales (máximo 500 caracteres)',
        }
    
    def __init__(self, *args, **kwargs):
        """
        Personaliza el formulario según el contexto.
        """
        super().__init__(*args, **kwargs)
        
        # Filtrar solo carreras activas
        self.fields['carrera'].queryset = Carrera.objects.filter(
            activa=True
        ).order_by('nombre')
        
        # Hacer carrera opcional pero recomendada
        self.fields['carrera'].required = False
        self.fields['carrera'].empty_label = "Seleccionar carrera..."
        
        # Configurar fecha por defecto
        if not self.instance.pk:  # Solo para nuevos alumnos
            self.fields['fecha_ingreso'].initial = timezone.now().date()
        
        # Agregar clases CSS adicionales
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            
            # Marcar campos requeridos visualmente
            if field.required:
                field.widget.attrs['class'] += ' required'
                if 'placeholder' in field.widget.attrs:
                    field.widget.attrs['placeholder'] += ' *'
    
    def clean_dni(self):
        """
        Validación personalizada para DNI.
        """
        dni = self.cleaned_data.get('dni')
        if not dni:
            raise ValidationError('El DNI es requerido.')
        
        # Limpiar espacios y caracteres no numéricos
        dni = re.sub(r'\D', '', dni)
        
        # Validar longitud
        if len(dni) < 7 or len(dni) > 8:
            raise ValidationError('El DNI debe tener entre 7 y 8 dígitos.')
        
        # Validar que no comience con 0
        if dni.startswith('0'):
            raise ValidationError('El DNI no puede comenzar con 0.')
        
        # Validar unicidad (excluyendo el registro actual en edición)
        queryset = Alumno.objects.filter(dni=dni)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            existing_alumno = queryset.first()
            raise ValidationError(
                f'El DNI {dni} ya está registrado para {existing_alumno.nombre_completo}.'
            )
        
        return dni
    
    def clean_email(self):
        """
        Validación personalizada para email.
        """
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('El email es requerido.')
        
        # Normalizar a minúsculas
        email = email.lower().strip()
        
        # Validar unicidad (excluyendo el registro actual en edición)
        queryset = Alumno.objects.filter(email__iexact=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            existing_alumno = queryset.first()
            raise ValidationError(
                f'El email {email} ya está registrado para {existing_alumno.nombre_completo}.'
            )
        
        return email
    
    def clean_carrera(self):
        """
        Validación personalizada para carrera.
        """
        carrera = self.cleaned_data.get('carrera')
        
        if carrera and not carrera.activa:
            raise ValidationError(
                f'La carrera "{carrera.nombre}" no está activa. '
                'Seleccione una carrera activa.'
            )
        
        return carrera
    
    def clean_fecha_ingreso(self):
        """
        Validación personalizada para fecha de ingreso.
        """
        fecha_ingreso = self.cleaned_data.get('fecha_ingreso')
        
        if fecha_ingreso:
            # No puede ser futura
            if fecha_ingreso > timezone.now().date():
                raise ValidationError('La fecha de ingreso no puede ser futura.')
            
            # No puede ser muy antigua (ejemplo: más de 50 años)
            año_minimo = timezone.now().year - 50
            if fecha_ingreso.year < año_minimo:
                raise ValidationError(f'La fecha de ingreso no puede ser anterior a {año_minimo}.')
        
        return fecha_ingreso
    
    def clean(self):
        """
        Validaciones que involucran múltiples campos.
        """
        cleaned_data = super().clean()
        
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        
        # Validar que nombre y apellido no sean iguales
        if first_name and last_name and first_name.lower() == last_name.lower():
            raise ValidationError(
                'El nombre y apellido no pueden ser idénticos.'
            )
        
        return cleaned_data
    
    @property
    def media(self):
        """
        Archivos CSS y JavaScript adicionales para el formulario.
        """
        return forms.Media(
            css={
                'all': ['students/css/alumno_form.css']
            },
            js=[
                'students/js/alumno_form.js',
                'students/js/validation.js'
            ]
        )


class AlumnoBusquedaForm(forms.Form):
    """
    Formulario para búsqueda avanzada de alumnos.
    """
    
    ESTADO_CHOICES = [
        ('', 'Todos'),
        ('true', 'Activos'),
        ('false', 'Inactivos'),
    ]
    
    search = forms.CharField(
        label='Búsqueda',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, apellido, DNI, legajo...',
        })
    )
    
    carrera = forms.ModelChoiceField(
        label='Carrera',
        queryset=Carrera.objects.filter(activa=True).order_by('nombre'),
        required=False,
        empty_label='Todas las carreras',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    activo = forms.ChoiceField(
        label='Estado',
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    fecha_ingreso_desde = forms.DateField(
        label='Ingreso desde',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    fecha_ingreso_hasta = forms.DateField(
        label='Ingreso hasta',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': timezone.now().date().isoformat(),
        })
    )
    
    def clean(self):
        """
        Validar que la fecha desde sea menor que fecha hasta.
        """
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_ingreso_desde')
        fecha_hasta = cleaned_data.get('fecha_ingreso_hasta')
        
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError(
                'La fecha "desde" debe ser anterior a la fecha "hasta".'
            )
        
        return cleaned_data


class AlumnoRapidoForm(forms.ModelForm):
    """
    Formulario simplificado para registro rápido de alumnos.
    Solo campos esenciales.
    """
    
    class Meta:
        model = Alumno
        fields = ['first_name', 'last_name', 'dni', 'email', 'carrera']
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Nombre *',
                'autofocus': True,
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Apellido *',
            }),
            'dni': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'DNI *',
                'maxlength': 8,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Email *',
            }),
            'carrera': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Solo carreras activas
        self.fields['carrera'].queryset = Carrera.objects.filter(
            activa=True
        ).order_by('nombre')
        self.fields['carrera'].empty_label = "Seleccionar carrera..."
        
        # Todos los campos son requeridos en el formulario rápido
        for field in self.fields.values():
            field.required = True


class AlumnoImportForm(forms.Form):
    """
    Formulario para importar alumnos desde archivo CSV.
    """
    
    archivo_csv = forms.FileField(
        label='Archivo CSV',
        help_text='Archivo CSV con columnas: nombre, apellido, dni, email, carrera_codigo',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv',
        })
    )
    
    sobrescribir_existentes = forms.BooleanField(
        label='Sobrescribir alumnos existentes',
        required=False,
        help_text='Si está marcado, actualizará alumnos con DNI existente',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    def clean_archivo_csv(self):
        """
        Validar que el archivo sea CSV y tenga tamaño apropiado.
        """
        archivo = self.cleaned_data.get('archivo_csv')
        
        if archivo:
            # Validar extensión
            if not archivo.name.endswith('.csv'):
                raise ValidationError('El archivo debe tener extensión .csv')
            
            # Validar tamaño (máximo 5MB)
            if archivo.size > 5 * 1024 * 1024:
                raise ValidationError('El archivo no puede superar los 5MB')
        
        return archivo
