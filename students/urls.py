from django.urls import path
from .views import (
    AlumnoListView, AlumnoDetailView, AlumnoCreateView, AlumnoUpdateView, AlumnoDeleteView
)

app_name = 'students'

urlpatterns = [
    path('', AlumnoListView.as_view(), name='alumno_list'),
    path('<int:pk>/', AlumnoDetailView.as_view(), name='alumno_detail'),
    path('crear/', AlumnoCreateView.as_view(), name='alumno_create'),
    path('<int:pk>/editar/', AlumnoUpdateView.as_view(), name='alumno_update'),
    path('<int:pk>/eliminar/', AlumnoDeleteView.as_view(), name='alumno_delete'),
]
