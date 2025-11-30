from django.urls import path
from .views import (
    CarreraListView, CarreraDetailView, CarreraCreateView, CarreraUpdateView, CarreraDeleteView,
    MateriaListView, MateriaDetailView, MateriaCreateView, MateriaUpdateView, MateriaDeleteView
)

app_name = 'escuelas'

urlpatterns = [
    # Carreras
    path('', CarreraListView.as_view(), name='carrera_list'),
    path('<int:pk>/', CarreraDetailView.as_view(), name='carrera_detail'),
    path('crear/', CarreraCreateView.as_view(), name='carrera_create'),
    path('<int:pk>/editar/', CarreraUpdateView.as_view(), name='carrera_update'),
    path('<int:pk>/eliminar/', CarreraDeleteView.as_view(), name='carrera_delete'),
    
    # Materias
    path('materias/', MateriaListView.as_view(), name='materia_list'),
    path('materias/<int:pk>/', MateriaDetailView.as_view(), name='materia_detail'),
    path('materias/crear/', MateriaCreateView.as_view(), name='materia_create'),
    path('materias/<int:pk>/editar/', MateriaUpdateView.as_view(), name='materia_update'),
    path('materias/<int:pk>/eliminar/', MateriaDeleteView.as_view(), name='materia_delete'),
]
