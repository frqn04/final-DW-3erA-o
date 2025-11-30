from django.urls import path
from .views import (
    InscripcionListView, InscripcionDetailView, InscripcionCreateView, 
    InscripcionUpdateView, InscripcionDeleteView
)

app_name = 'enrollments'

urlpatterns = [
    path('', InscripcionListView.as_view(), name='inscripcion_list'),
    path('<int:pk>/', InscripcionDetailView.as_view(), name='inscripcion_detail'),
    path('crear/', InscripcionCreateView.as_view(), name='inscripcion_create'),
    path('<int:pk>/editar/', InscripcionUpdateView.as_view(), name='inscripcion_update'),
    path('<int:pk>/eliminar/', InscripcionDeleteView.as_view(), name='inscripcion_delete'),
]
