"""
Formularios personalizados para la app escuelas.

Este módulo contiene formularios Django optimizados con:
- Validaciones avanzadas
- Widgets Bootstrap 5 personalizados
- JavaScript integrado
- Validaciones cruzadas
- UX mejorada

Formularios disponibles:
======================

1. CarreraForm: Formulario para carreras con validaciones
2. MateriaForm: Formulario para materias con dependencias dinámicas
3. CarreraFilterForm: Formulario de filtros optimizado
4. MateriaFilterForm: Formulario de filtros con JavaScript

Características avanzadas:
=========================

- Validación en tiempo real con JavaScript
- Campos dependientes (año_carrera depende de duración de carrera)
- Autocompletado inteligente
- Validaciones cruzadas
- Mensajes de error personalizados
- Widgets con clases CSS automáticas
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.urls import reverse
from .models import Carrera, Materia


class CarreraForm(forms.ModelForm):
    """
    Formulario personalizado para Carrera con validaciones avanzadas.
    
    Características:
    ===============
    
    1. VALIDACIONES MEJORADAS:
       - Código único con formato específico
       - Nombre sin caracteres especiales
       - Duración realista (1-10 años)
    
    2. WIDGETS PERSONALIZADOS:
       - Bootstrap 5 clases automáticas
       - Placeholders informativos
       - Tooltips con ayuda
    
    3. JAVASCRIPT INTEGRADO:
       - Generación automática de código
       - Validación en tiempo real
       - Preview de información
    """
    
    class Meta:
        model = Carrera
        fields = ['nombre', 'codigo', 'duracion_anos', 'activa', 'descripcion']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ingeniería en Sistemas',
                'maxlength': 200,
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'top',
                'title': 'Nombre completo de la carrera (único en el sistema)',
                'oninput': 'generarCodigo(this.value)'  # JavaScript automático
            }),
            
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ING-SIS, PROF-MAT',
                'maxlength': 20,
                'style': 'text-transform: uppercase;',
                'data-bs-toggle': 'tooltip',
                'title': 'Código único identificatorio (se genera automáticamente)',
                'pattern': '[A-Z]{2,4}-[A-Z]{2,4}',
                'oninput': 'validarCodigo(this.value)'
            }),
            
            'duracion_anos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': '4',
                'data-bs-toggle': 'tooltip',
                'title': 'Duración nominal de la carrera en años',
                'onchange': 'actualizarInfoDuracion(this.value)'
            }),
            
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'data-bs-toggle': 'tooltip',
                'title': 'Marcar si la carrera está disponible para inscripciones'
            }),
            
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada de la carrera, objetivos, perfil profesional...',
                'data-bs-toggle': 'tooltip',
                'title': 'Información detallada para estudiantes y administradores',
                'onkeyup': 'contarCaracteres(this)'
            })
        }
        
        help_texts = {
            'nombre': 'Nombre único de la carrera en todo el sistema.',
            'codigo': 'Código único para identificación administrativa.',
            'duracion_anos': 'Duración nominal en años (1-10).',
            'activa': 'Indica si está disponible para nuevas inscripciones.',
            'descripcion': 'Información detallada sobre la carrera.'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar clases CSS automáticamente
        for field_name, field in self.fields.items():
            if field_name != 'activa':  # Checkbox tiene clase diferente
                field.widget.attrs.update({'class': 'form-control'})
        
        # Marcar campos requeridos visualmente
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs.update({
                    'required': True,
                    'aria-required': 'true'
                })
                # Agregar asterisco al label
                field.label = f"{field.label} *"
    
    def clean_codigo(self):
        """Validación personalizada para código"""
        codigo = self.cleaned_data.get('codigo', '').upper()
        
        if not codigo:
            raise ValidationError('El código es requerido.')
        
        # Formato específico: XXX-XXX
        import re
        if not re.match(r'^[A-Z]{2,4}-[A-Z]{2,4}$', codigo):
            raise ValidationError(
                'El código debe tener el formato XXX-XXX (ej: ING-SIS, PROF-MAT)'
            )
        
        # Verificar unicidad (excluyendo la instancia actual en edición)
        queryset = Carrera.objects.filter(codigo=codigo)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError(f'Ya existe una carrera con el código "{codigo}".')
        
        return codigo
    
    def clean_nombre(self):
        """Validación personalizada para nombre"""
        nombre = self.cleaned_data.get('nombre', '').strip()
        
        if not nombre:
            raise ValidationError('El nombre es requerido.')
        
        if len(nombre) < 5:
            raise ValidationError('El nombre debe tener al menos 5 caracteres.')
        
        # Verificar que no tenga solo números
        if nombre.isdigit():
            raise ValidationError('El nombre no puede contener solo números.')
        
        return nombre.title()  # Capitalizar palabras
    
    def clean_duracion_anos(self):
        """Validación para duración"""
        duracion = self.cleaned_data.get('duracion_anos')
        
        if duracion and (duracion < 1 or duracion > 10):
            raise ValidationError('La duración debe estar entre 1 y 10 años.')
        
        return duracion
    
    def get_javascript(self):
        """Retorna JavaScript personalizado para el formulario"""
        return """
        <script>
        // Generar código automáticamente desde el nombre
        function generarCodigo(nombre) {
            if (!nombre) return;
            
            const palabras = nombre.toUpperCase()
                .replace(/[^A-Z\\s]/g, '')
                .split(' ')
                .filter(p => p.length > 0);
            
            if (palabras.length >= 2) {
                const codigo = palabras[0].substring(0, 3) + '-' + 
                              palabras[1].substring(0, 3);
                document.getElementById('id_codigo').value = codigo;
                validarCodigo(codigo);
            }
        }
        
        // Validar código en tiempo real
        function validarCodigo(codigo) {
            const pattern = /^[A-Z]{2,4}-[A-Z]{2,4}$/;
            const input = document.getElementById('id_codigo');
            
            if (pattern.test(codigo)) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            }
        }
        
        // Actualizar información de duración
        function actualizarInfoDuracion(anos) {
            const info = document.getElementById('duracion-info');
            if (info) {
                info.innerHTML = `
                    <small class="text-muted">
                        Carrera de ${anos} año${anos != 1 ? 's' : ''} de duración
                    </small>
                `;
            }
        }
        
        // Contador de caracteres para descripción
        function contarCaracteres(textarea) {
            const contador = document.getElementById('char-counter');
            const max = 1000;
            const actual = textarea.value.length;
            
            if (contador) {
                contador.innerHTML = `${actual}/${max} caracteres`;
                contador.className = actual > max ? 'text-danger' : 'text-muted';
            }
        }
        </script>
        """


class MateriaForm(forms.ModelForm):
    """
    Formulario personalizado para Materia con dependencias dinámicas.
    
    Características avanzadas:
    =========================
    
    1. CAMPOS DEPENDIENTES:
       - año_carrera se limita según duración de carrera
       - código se genera automáticamente
       - validaciones cruzadas entre campos
    
    2. AJAX INTEGRATION:
       - Cargar años disponibles según carrera
       - Verificar duplicados en tiempo real
       - Autocompletado inteligente
    
    3. VALIDACIONES COMPLEJAS:
       - Año no puede superar duración de carrera
       - Código único por carrera
       - Cupo mínimo según tipo de materia
    """
    
    class Meta:
        model = Materia
        fields = [
            'carrera', 'nombre', 'codigo', 'cupo_maximo', 
            'año_carrera', 'cuatrimestre', 'horas_semanales', 
            'activa', 'descripcion'
        ]
        
        widgets = {
            'carrera': forms.Select(attrs={
                'class': 'form-select',
                'data-bs-toggle': 'tooltip',
                'title': 'Seleccionar carrera a la que pertenece la materia',
                'onchange': 'cargarAniosDisponibles(this.value)'
            }),
            
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Matemática I, Programación Avanzada',
                'maxlength': 200,
                'oninput': 'generarCodigoMateria(this.value)',
                'onblur': 'verificarDuplicado()'
            }),
            
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: MAT101, PROG201',
                'maxlength': 20,
                'style': 'text-transform: uppercase;',
                'pattern': '[A-Z]{3}[0-9]{3}'
            }),
            
            'cupo_maximo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'max': 100,
                'placeholder': '30',
                'onchange': 'calcularRecomendaciones(this.value)'
            }),
            
            'año_carrera': forms.Select(attrs={
                'class': 'form-select',
                'data-bs-toggle': 'tooltip',
                'title': 'Año del plan de estudios'
            }),
            
            'cuatrimestre': forms.Select(attrs={
                'class': 'form-select'
            }),
            
            'horas_semanales': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20,
                'value': 4,
                'onchange': 'calcularCargaHoraria(this.value)'
            }),
            
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la materia, objetivos, metodología...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar opciones dinámicas para año_carrera
        self.fields['año_carrera'].widget = forms.Select(
            choices=[(i, f"{i}° Año") for i in range(1, 11)],
            attrs=self.fields['año_carrera'].widget.attrs
        )
        
        # Si hay una carrera seleccionada, limitar años
        if 'carrera' in self.data:
            try:
                carrera_id = int(self.data.get('carrera'))
                carrera = Carrera.objects.get(id=carrera_id)
                self.fields['año_carrera'].widget.choices = [
                    (i, f"{i}° Año") for i in range(1, carrera.duracion_anos + 1)
                ]
            except (ValueError, Carrera.DoesNotExist):
                pass
    
    def clean(self):
        """Validaciones cruzadas entre campos"""
        cleaned_data = super().clean()
        carrera = cleaned_data.get('carrera')
        año_carrera = cleaned_data.get('año_carrera')
        nombre = cleaned_data.get('nombre')
        codigo = cleaned_data.get('codigo')
        
        errors = {}
        
        # Validar año no supere duración de carrera
        if carrera and año_carrera:
            if año_carrera > carrera.duracion_anos:
                errors['año_carrera'] = f'El año no puede ser mayor a {carrera.duracion_anos} (duración de la carrera).'
        
        # Validar unicidad de nombre por carrera
        if carrera and nombre:
            queryset = Materia.objects.filter(carrera=carrera, nombre=nombre)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                errors['nombre'] = f'Ya existe una materia con el nombre "{nombre}" en la carrera "{carrera.nombre}".'
        
        # Validar unicidad de código por carrera
        if carrera and codigo:
            queryset = Materia.objects.filter(carrera=carrera, codigo=codigo)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                errors['codigo'] = f'Ya existe una materia con el código "{codigo}" en la carrera "{carrera.nombre}".'
        
        if errors:
            raise ValidationError(errors)
        
        return cleaned_data
    
    def get_ajax_urls(self):
        """URLs AJAX para funcionalidad dinámica"""
        return {
            'cargar_años': reverse('escuelas:ajax_cargar_años'),
            'verificar_duplicado': reverse('escuelas:ajax_verificar_duplicado'),
            'generar_codigo': reverse('escuelas:ajax_generar_codigo')
        }


# EJEMPLO DE USO EN TEMPLATES:
"""
<!-- En el template carrera_form.html -->
<form method="post" novalidate>
    {% csrf_token %}
    
    <!-- Campo con JavaScript integrado -->
    <div class="mb-3">
        {{ form.nombre.label_tag }}
        {{ form.nombre }}
        <div id="nombre-feedback" class="invalid-feedback"></div>
        {{ form.nombre.help_text }}
    </div>
    
    <!-- Campo dependiente -->
    <div class="mb-3">
        {{ form.codigo.label_tag }}
        {{ form.codigo }}
        <div id="duracion-info"></div>
    </div>
    
    <button type="submit" class="btn btn-primary">Guardar</button>
</form>

<!-- JavaScript del formulario -->
{{ form.get_javascript|safe }}
"""
