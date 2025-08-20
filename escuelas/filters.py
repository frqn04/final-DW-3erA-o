"""
Filtros para la app escuelas.

Este módulo contiene los filtros personalizados usando django-filter
para facilitar la búsqueda y filtrado de modelos en las vistas.

Integración con FilterView:
==========================

Para usar estos filtros en las vistas, se integran con django_filters.views.FilterView:

Ejemplo de uso en views.py:
```python
from django_filters.views import FilterView
from .filters import MateriaFilter
from .models import Materia

class MateriaListView(FilterView):
    model = Materia
    filterset_class = MateriaFilter
    template_name = 'escuelas/materia_list.html'
    context_object_name = 'materias'
    paginate_by = 20
```

En el template (materia_list.html):
```html
<form method="get">
    {{ filter.form.as_p }}
    <button type="submit">Filtrar</button>
</form>

{% for materia in materias %}
    <!-- Mostrar materias filtradas -->
{% endfor %}
```

URLs:
```python
path('materias/', views.MateriaListView.as_view(), name='materia_list'),
```
"""

import django_filters
from django import forms
from django.db.models import Q, Count, Case, When, IntegerField
from .models import Materia, Carrera


class MateriaFilter(django_filters.FilterSet):
    """
    Filtro personalizado para materias con opciones avanzadas de búsqueda.
    
    Características:
    - Filtro por carrera usando ModelChoiceFilter
    - Filtro por cupo disponible (inscriptos < cupo_maximo)
    - Filtros adicionales para mejor funcionalidad
    """
    
    # REQUERIMIENTO: Filtro por carrera usando ModelChoiceFilter
    carrera = django_filters.ModelChoiceFilter(
        queryset=Carrera.objects.all(),
        field_name='carrera',
        to_field_name='id',
        empty_label='Todas las carreras',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Seleccionar carrera'
        }),
        help_text='Filtrar materias por carrera específica'
    )
    
    # REQUERIMIENTO: Filtro por cupo disponible (inscriptos < cupo_maximo)
    cupo_disponible = django_filters.BooleanFilter(
        method='filter_cupo_disponible',
        label='Solo materias con cupo disponible',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        help_text='Mostrar solo materias que tienen cupos libres'
    )
    
    # Filtros adicionales optimizados
    nombre = django_filters.CharFilter(
        field_name='nombre',
        lookup_expr='icontains',
        label='Buscar por nombre',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribir nombre de materia...'
        })
    )
    
    año_carrera = django_filters.NumberFilter(
        field_name='año_carrera',
        label='Año de carrera',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 1, 2, 3...',
            'min': '1'
        })
    )
    
    cuatrimestre = django_filters.ChoiceFilter(
        field_name='cuatrimestre',
        choices=[(0, 'Anual'), (1, '1° Cuatrimestre'), (2, '2° Cuatrimestre')],
        empty_label='Todos los cuatrimestres',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    activa = django_filters.BooleanFilter(
        field_name='activa',
        label='Solo materias activas',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    cupo_maximo_min = django_filters.NumberFilter(
        field_name='cupo_maximo',
        lookup_expr='gte',
        label='Cupo mínimo',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 20',
            'min': '1'
        })
    )
    
    cupo_maximo_max = django_filters.NumberFilter(
        field_name='cupo_maximo',
        lookup_expr='lte',
        label='Cupo máximo',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 50',
            'min': '1'
        })
    )
    
    def filter_cupo_disponible(self, queryset, name, value):
        """
        Filtro personalizado para materias con cupo disponible.
        
        LÓGICA DEL FILTRO:
        ==================
        
        1. Si value=True: Mostrar solo materias donde inscriptos < cupo_maximo
        2. Si value=False o None: Mostrar todas las materias
        
        IMPLEMENTACIÓN ACTUAL:
        ======================
        
        Como aún no tenemos el modelo de inscripciones implementado,
        este filtro actualmente devuelve todas las materias cuando value=True.
        
        IMPLEMENTACIÓN FUTURA:
        ======================
        
        Cuando implementemos el modelo de inscripciones, el código será:
        
        ```python
        if value:
            return queryset.annotate(
                inscriptos_count=Count('inscripciones')
            ).filter(
                inscriptos_count__lt=models.F('cupo_maximo')
            )
        return queryset
        ```
        
        EXPLICACIÓN DE LA ANOTACIÓN:
        ===========================
        
        1. annotate(inscriptos_count=Count('inscripciones')):
           - Cuenta las inscripciones relacionadas a cada materia
           - Agrega un campo virtual 'inscriptos_count' al queryset
        
        2. filter(inscriptos_count__lt=models.F('cupo_maximo')):
           - Filtra materias donde inscriptos < cupo_maximo
           - F('cupo_maximo') permite comparar con campos de la misma tabla
        
        3. BENEFICIOS:
           - Eficiente: Una sola consulta SQL con JOIN
           - Dinámico: Se actualiza automáticamente
           - Escalable: Funciona con miles de registros
        """
        
        if value:
            # TODO: Implementar cuando tengamos el modelo de inscripciones
            # Por ahora devolvemos todas las materias
            # 
            # Código futuro:
            # return queryset.annotate(
            #     inscriptos_count=Count('inscripciones')
            # ).filter(
            #     inscriptos_count__lt=models.F('cupo_maximo')
            # )
            
            # Simulación temporal: asumimos que todas tienen cupo disponible
            return queryset
        
        return queryset
    
    class Meta:
        model = Materia
        fields = []  # Usamos campos personalizados definidos arriba
    
    def __init__(self, *args, **kwargs):
        """
        Inicialización personalizada del filtro.
        
        Aquí podemos:
        - Modificar querysets dinámicamente
        - Personalizar widgets según el usuario
        - Agregar validaciones adicionales
        """
        super().__init__(*args, **kwargs)
        
        # Optimizar queryset de carreras para mejor performance
        self.filters['carrera'].queryset = Carrera.objects.select_related().order_by('nombre')
        
        # Personalizar etiquetas según el contexto
        if hasattr(self, 'request') and self.request.user.is_authenticated:
            # Si el usuario está autenticado, podemos personalizar más
            pass


class CarreraFilter(django_filters.FilterSet):
    """
    Filtro básico para carreras con opciones mejoradas.
    """
    
    nombre = django_filters.CharFilter(
        field_name='nombre',
        lookup_expr='icontains',
        label='Buscar por nombre',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribir nombre de carrera...'
        })
    )
    
    codigo = django_filters.CharFilter(
        field_name='codigo',
        lookup_expr='icontains',
        label='Buscar por código',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: ING-SIS, PROF-MAT...'
        })
    )
    
    duracion_anos = django_filters.NumberFilter(
        field_name='duracion_anos',
        label='Duración en años',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 4',
            'min': '1'
        })
    )
    
    activa = django_filters.BooleanFilter(
        field_name='activa',
        label='Solo carreras activas',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    class Meta:
        model = Carrera
        fields = []


# Ejemplo de uso avanzado con FilterView personalizada
"""
INTEGRACIÓN COMPLETA CON FILTERVIEW:
===================================

1. En views.py:
```python
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from .filters import MateriaFilter
from .models import Materia

class MateriaListView(LoginRequiredMixin, FilterView):
    model = Materia
    filterset_class = MateriaFilter
    template_name = 'escuelas/materia_list.html'
    context_object_name = 'materias'
    paginate_by = 20
    
    def get_queryset(self):
        # Optimizar queryset base
        return Materia.objects.select_related('carrera').order_by('carrera__nombre', 'nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_materias'] = self.get_queryset().count()
        return context
```

2. En urls.py:
```python
from django.urls import path
from . import views

app_name = 'escuelas'

urlpatterns = [
    path('materias/', views.MateriaListView.as_view(), name='materia_list'),
]
```

3. En templates/escuelas/materia_list.html:
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block content %}
<div class="container">
    <h2>Listado de Materias</h2>
    
    <!-- Formulario de filtros -->
    <div class="card mb-4">
        <div class="card-body">
            <form method="get" class="row g-3">
                <div class="col-md-4">
                    {{ filter.form.carrera|as_crispy_field }}
                </div>
                <div class="col-md-4">
                    {{ filter.form.nombre|as_crispy_field }}
                </div>
                <div class="col-md-4">
                    {{ filter.form.cupo_disponible|as_crispy_field }}
                </div>
                <div class="col-12">
                    <button type="submit" class="btn btn-primary">Filtrar</button>
                    <a href="{% url 'escuelas:materia_list' %}" class="btn btn-secondary">Limpiar</a>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Resultados -->
    <div class="row">
        {% for materia in materias %}
        <div class="col-md-6 col-lg-4 mb-3">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">{{ materia.nombre }}</h5>
                    <p class="card-text">
                        <strong>Carrera:</strong> {{ materia.carrera.nombre }}<br>
                        <strong>Cupo:</strong> {{ materia.cupo_maximo }}
                    </p>
                </div>
            </div>
        </div>
        {% empty %}
        <div class="col-12">
            <div class="alert alert-info">
                No se encontraron materias con los filtros aplicados.
            </div>
        </div>
        {% endfor %}
    </div>
    
    <!-- Paginación -->
    {% if is_paginated %}
    <nav>
        <ul class="pagination justify-content-center">
            {% if page_obj.has_previous %}
                <li class="page-item">
                    <a class="page-link" href="?{{ filter.form.as_url_params }}&page={{ page_obj.previous_page_number }}">Anterior</a>
                </li>
            {% endif %}
            
            <li class="page-item active">
                <span class="page-link">Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}</span>
            </li>
            
            {% if page_obj.has_next %}
                <li class="page-item">
                    <a class="page-link" href="?{{ filter.form.as_url_params }}&page={{ page_obj.next_page_number }}">Siguiente</a>
                </li>
            {% endif %}
        </ul>
    </nav>
    {% endif %}
</div>
{% endblock %}
```

VENTAJAS DE USAR FilterView:
===========================

1. AUTOMATIZACIÓN: 
   - Genera formularios automáticamente
   - Aplica filtros sin código adicional
   - Mantiene estado en URLs

2. PERFORMANCE:
   - Queryset eficiente con select_related
   - Paginación automática
   - Lazy loading de filtros

3. UX/UI:
   - URLs amigables con parámetros
   - Estado persistente
   - Integración con Bootstrap

4. MANTENIMIENTO:
   - Código limpio y reutilizable
   - Fácil extensión de filtros
   - Separación de responsabilidades
"""
