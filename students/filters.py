"""
Filtros avanzados para la app students usando django-filter.

Proporciona filtrado dinámico y búsqueda avanzada para la gestión
de alumnos con interfaz intuitiva y rendimiento optimizado.

Características implementadas:
- Filtrado por múltiples campos
- Búsqueda por texto completo
- Filtros de rango de fechas
- Filtros por estado y carrera
- Ordenamiento dinámico
- Filtros personalizados con widgets optimizados
"""

import django_filters
from django import forms
from django.db.models import Q
from django.utils import timezone

from .models import Alumno
from escuelas.models import Carrera


class AlumnoFilter(django_filters.FilterSet):
    """
    Filtros avanzados para el modelo Alumno.
    
    Proporciona búsqueda por texto, filtrado por fechas,
    estado, carrera y otros campos relevantes.
    """
    
    # Búsqueda por texto en múltiples campos
    search = django_filters.CharFilter(
        method='filter_search',
        label='Búsqueda general',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, apellido, DNI, legajo, email...',
            'autocomplete': 'off',
        })
    )
    
    # Filtro por carrera
    carrera = django_filters.ModelChoiceFilter(
        queryset=Carrera.objects.filter(activa=True).order_by('nombre'),
        empty_label='Todas las carreras',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    # Filtro por estado activo/inactivo
    activo = django_filters.BooleanFilter(
        label='Estado',
        widget=forms.Select(
            choices=[
                ('', 'Todos los estados'),
                (True, 'Activos'),
                (False, 'Inactivos'),
            ],
            attrs={
                'class': 'form-select',
            }
        )
    )
    
    # Filtro por rango de fechas de ingreso
    fecha_ingreso = django_filters.DateFromToRangeFilter(
        label='Fecha de ingreso',
        widget=django_filters.widgets.RangeWidget(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    # Filtro por año de ingreso
    año_ingreso = django_filters.NumberFilter(
        field_name='fecha_ingreso__year',
        label='Año de ingreso',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYYY',
            'min': timezone.now().year - 50,
            'max': timezone.now().year,
        })
    )
    
    # Filtro por años en la institución
    años_institucion = django_filters.RangeFilter(
        method='filter_años_institucion',
        label='Años en institución',
        widget=django_filters.widgets.RangeWidget(attrs={
            'class': 'form-control',
            'placeholder': 'Desde - Hasta',
            'min': 0,
        })
    )
    
    # Filtro por primera letra del apellido
    apellido_inicial = django_filters.CharFilter(
        field_name='last_name',
        lookup_expr='istartswith',
        label='Apellido inicia con',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: M',
            'maxlength': 1,
            'style': 'text-transform: uppercase;',
        })
    )
    
    # Filtro por rango de DNI
    dni_range = django_filters.RangeFilter(
        field_name='dni',
        label='Rango de DNI',
        widget=django_filters.widgets.RangeWidget(attrs={
            'class': 'form-control',
            'placeholder': 'Desde - Hasta',
        })
    )
    
    # Filtro por legajo
    legajo = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Legajo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar legajo...',
        })
    )
    
    # Ordenamiento
    ordering = django_filters.OrderingFilter(
        fields=(
            ('last_name', 'apellido'),
            ('first_name', 'nombre'),
            ('legajo', 'legajo'),
            ('dni', 'dni'),
            ('fecha_ingreso', 'fecha_ingreso'),
            ('carrera__nombre', 'carrera'),
            ('created_at', 'fecha_registro'),
            ('updated_at', 'ultima_modificacion'),
        ),
        field_labels={
            'last_name': 'Apellido',
            'first_name': 'Nombre',
            'legajo': 'Legajo',
            'dni': 'DNI',
            'fecha_ingreso': 'Fecha de Ingreso',
            'carrera__nombre': 'Carrera',
            'created_at': 'Fecha de Registro',
            'updated_at': 'Última Modificación',
        },
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        empty_label='Ordenar por...',
    )
    
    class Meta:
        model = Alumno
        fields = []  # Usamos filtros personalizados
    
    def filter_search(self, queryset, name, value):
        """
        Búsqueda por texto en múltiples campos.
        """
        if not value:
            return queryset
        
        # Limpiar el valor de búsqueda
        search_terms = value.strip().split()
        
        if not search_terms:
            return queryset
        
        # Construir consulta Q para cada término
        search_query = Q()
        
        for term in search_terms:
            term_query = (
                Q(first_name__icontains=term) |
                Q(last_name__icontains=term) |
                Q(dni__icontains=term) |
                Q(legajo__icontains=term) |
                Q(email__icontains=term) |
                Q(carrera__nombre__icontains=term) |
                Q(carrera__codigo__icontains=term)
            )
            
            # AND entre términos (todos deben coincidir)
            if search_query:
                search_query &= term_query
            else:
                search_query = term_query
        
        return queryset.filter(search_query)
    
    def filter_años_institucion(self, queryset, name, value):
        """
        Filtro por años en la institución.
        """
        if not value:
            return queryset
        
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        
        today = timezone.now().date()
        
        if value.start is not None:
            fecha_max = today - relativedelta(years=int(value.start))
            queryset = queryset.filter(fecha_ingreso__lte=fecha_max)
        
        if value.stop is not None:
            fecha_min = today - relativedelta(years=int(value.stop))
            queryset = queryset.filter(fecha_ingreso__gte=fecha_min)
        
        return queryset
    
    @property
    def qs(self):
        """
        Optimiza las consultas con select_related y prefetch_related.
        """
        queryset = super().qs
        return queryset.select_related('carrera').order_by('last_name', 'first_name')


class AlumnoReporteFilter(django_filters.FilterSet):
    """
    Filtros específicos para generar reportes de alumnos.
    Versión simplificada enfocada en reportes.
    """
    
    carrera = django_filters.ModelMultipleChoiceFilter(
        queryset=Carrera.objects.filter(activa=True).order_by('nombre'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
        }),
        label='Carreras a incluir'
    )
    
    activo = django_filters.BooleanFilter(
        widget=forms.Select(
            choices=[
                ('', 'Todos'),
                (True, 'Solo activos'),
                (False, 'Solo inactivos'),
            ],
            attrs={'class': 'form-select'}
        )
    )
    
    fecha_ingreso = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    class Meta:
        model = Alumno
        fields = ['carrera', 'activo', 'fecha_ingreso']


class AlumnoExportFilter(django_filters.FilterSet):
    """
    Filtros para exportación de datos de alumnos.
    Incluye filtros adicionales para selección masiva.
    """
    
    # Todos los filtros básicos
    carrera = django_filters.ModelChoiceFilter(
        queryset=Carrera.objects.all().order_by('nombre'),
        empty_label='Todas las carreras'
    )
    
    activo = django_filters.BooleanFilter()
    
    fecha_ingreso = django_filters.DateFromToRangeFilter()
    
    # Filtros específicos para exportación
    incluir_observaciones = django_filters.BooleanFilter(
        method='filter_dummy',  # No filtra, solo para UI
        label='Incluir observaciones en export',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'checked': True,
        })
    )
    
    formato_export = django_filters.ChoiceFilter(
        method='filter_dummy',  # No filtra, solo para UI
        choices=[
            ('csv', 'CSV'),
            ('excel', 'Excel'),
            ('pdf', 'PDF'),
        ],
        label='Formato de exportación',
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        initial='csv'
    )
    
    class Meta:
        model = Alumno
        fields = ['carrera', 'activo', 'fecha_ingreso']
    
    def filter_dummy(self, queryset, name, value):
        """
        Filtro dummy que no modifica el queryset.
        Usado para campos de UI que no filtran datos.
        """
        return queryset


class AlumnoAdminFilter(django_filters.FilterSet):
    """
    Filtros específicos para la interfaz administrativa.
    Incluye filtros técnicos y de auditoría.
    """
    
    # Filtros básicos
    search = django_filters.CharFilter(
        method='filter_search',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Búsqueda rápida...',
        })
    )
    
    carrera = django_filters.ModelChoiceFilter(
        queryset=Carrera.objects.all().order_by('nombre'),
        empty_label='Todas',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
        })
    )
    
    activo = django_filters.BooleanFilter(
        widget=forms.Select(
            choices=[
                ('', 'Todos'),
                (True, 'Activos'),
                (False, 'Inactivos'),
            ],
            attrs={'class': 'form-select form-select-sm'}
        )
    )
    
    # Filtros de auditoría
    created_at = django_filters.DateFromToRangeFilter(
        label='Fecha de registro',
        widget=django_filters.widgets.RangeWidget(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date',
        })
    )
    
    updated_at = django_filters.DateFromToRangeFilter(
        label='Última modificación',
        widget=django_filters.widgets.RangeWidget(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date',
        })
    )
    
    # Filtro por usuarios que modificaron
    modified_recently = django_filters.BooleanFilter(
        method='filter_modified_recently',
        label='Modificados últimos 7 días',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    class Meta:
        model = Alumno
        fields = []
    
    def filter_search(self, queryset, name, value):
        """Búsqueda administrativa simplificada"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(dni__icontains=value) |
            Q(legajo__icontains=value)
        )
    
    def filter_modified_recently(self, queryset, name, value):
        """Filtrar registros modificados en los últimos 7 días"""
        if not value:
            return queryset
        
        fecha_limite = timezone.now() - timezone.timedelta(days=7)
        return queryset.filter(updated_at__gte=fecha_limite)
    
    @property
    def qs(self):
        """Optimizar consultas para admin"""
        queryset = super().qs
        return queryset.select_related('carrera')
