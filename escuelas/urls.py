"""
URLs para la app escuelas.

Este módulo define todas las rutas URL para las vistas CRUD de Carrera y Materia,
organizadas con namespace 'escuelas' para evitar conflictos.

Estructura de URLs:
==================

Carreras:
- /escuelas/carreras/                    -> Lista de carreras (filtros)
- /escuelas/carreras/crear/              -> Crear nueva carrera
- /escuelas/carreras/<id>/               -> Detalle de carrera
- /escuelas/carreras/<id>/editar/        -> Editar carrera
- /escuelas/carreras/<id>/eliminar/      -> Eliminar carrera

Materias:
- /escuelas/materias/                    -> Lista de materias (filtros)
- /escuelas/materias/crear/              -> Crear nueva materia
- /escuelas/materias/<id>/               -> Detalle de materia
- /escuelas/materias/<id>/editar/        -> Editar materia
- /escuelas/materias/<id>/eliminar/      -> Eliminar materia

Dashboard:
- /escuelas/                             -> Panel principal de escuelas
"""

from django.urls import path
from . import views

app_name = 'escuelas'

urlpatterns = [
    
    # ==========================================
    # DASHBOARD PRINCIPAL
    # ==========================================
    
    path('', views.EscuelasIndexView.as_view(), name='index'),
    
    
    # ==========================================
    # URLs PARA CARRERA
    # ==========================================
    
    # Lista de carreras con filtros
    path('carreras/', views.CarreraListView.as_view(), name='carrera_list'),
    
    # Crear nueva carrera
    path('carreras/crear/', views.CarreraCreateView.as_view(), name='carrera_create'),
    
    # Detalle de carrera específica
    path('carreras/<int:pk>/', views.CarreraDetailView.as_view(), name='carrera_detail'),
    
    # Editar carrera existente
    path('carreras/<int:pk>/editar/', views.CarreraUpdateView.as_view(), name='carrera_update'),
    
    # Eliminar carrera
    path('carreras/<int:pk>/eliminar/', views.CarreraDeleteView.as_view(), name='carrera_delete'),
    
    
    # ==========================================
    # URLs PARA MATERIA
    # ==========================================
    
    # Lista de materias con filtros avanzados
    path('materias/', views.MateriaListView.as_view(), name='materia_list'),
    
    # Crear nueva materia
    path('materias/crear/', views.MateriaCreateView.as_view(), name='materia_create'),
    
    # Detalle de materia específica
    path('materias/<int:pk>/', views.MateriaDetailView.as_view(), name='materia_detail'),
    
    # Editar materia existente
    path('materias/<int:pk>/editar/', views.MateriaUpdateView.as_view(), name='materia_update'),
    
    # Eliminar materia
    path('materias/<int:pk>/eliminar/', views.MateriaDeleteView.as_view(), name='materia_delete'),
]

"""
EJEMPLOS DE USO EN TEMPLATES:
============================

Enlaces con namespace:
```html
<!-- Dashboard principal -->
<a href="{% url 'escuelas:index' %}">Panel de Escuelas</a>

<!-- Carreras -->
<a href="{% url 'escuelas:carrera_list' %}">Ver Carreras</a>
<a href="{% url 'escuelas:carrera_create' %}">Nueva Carrera</a>
<a href="{% url 'escuelas:carrera_detail' pk=carrera.pk %}">Ver Carrera</a>
<a href="{% url 'escuelas:carrera_update' pk=carrera.pk %}">Editar Carrera</a>
<a href="{% url 'escuelas:carrera_delete' pk=carrera.pk %}">Eliminar Carrera</a>

<!-- Materias -->
<a href="{% url 'escuelas:materia_list' %}">Ver Materias</a>
<a href="{% url 'escuelas:materia_create' %}">Nueva Materia</a>
<a href="{% url 'escuelas:materia_detail' pk=materia.pk %}">Ver Materia</a>
<a href="{% url 'escuelas:materia_update' pk=materia.pk %}">Editar Materia</a>
<a href="{% url 'escuelas:materia_delete' pk=materia.pk %}">Eliminar Materia</a>
```

Redirects en vistas:
```python
from django.shortcuts import redirect

# Redireccionar a lista de carreras
return redirect('escuelas:carrera_list')

# Redireccionar a detalle específico
return redirect('escuelas:carrera_detail', pk=carrera.pk)
```

URLs con parámetros GET (filtros):
```
/escuelas/materias/?carrera=1&cupo_disponible=true&nombre=matematica
/escuelas/carreras/?nombre=ingenieria
```

INTEGRACIÓN CON EL PROYECTO PRINCIPAL:
=====================================

En el archivo principal urls.py del proyecto:
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('escuelas/', include('escuelas.urls')),  # ← Incluir estas URLs
]
```

Con esto, todas las URLs quedarán disponibles con el prefijo 'escuelas/':
- http://localhost:8000/escuelas/
- http://localhost:8000/escuelas/carreras/
- http://localhost:8000/escuelas/materias/
- etc.
"""
