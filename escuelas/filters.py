import django_filters
from .models import Materia, Carrera


class MateriaFilter(django_filters.FilterSet):
    """
    Filtro para materias con búsqueda por carrera y disponibilidad de cupo.
    """
    nombre = django_filters.CharFilter(lookup_expr='icontains', label='Nombre contiene')
    carrera = django_filters.ModelChoiceFilter(queryset=Carrera.objects.all(), label='Carrera')
    año_carrera = django_filters.NumberFilter(label='Año de carrera')
    
    class Meta:
        model = Materia
        fields = ['nombre', 'carrera', 'año_carrera', 'activa']

