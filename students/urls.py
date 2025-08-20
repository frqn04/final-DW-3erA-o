"""
URLs para la aplicación students - MVP optimizado.

Define las rutas esenciales + mejoras de UX estratégicas:
- CRUD completo
- Dashboard con estadísticas
- Búsqueda AJAX para mejor UX

Patrones implementados:
- RESTful naming conventions
- Namespace 'students'  
- URLs semánticas y amigables
- Progressive Enhancement (MVP → Full)
"""

from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    
    # === CRUD PRINCIPAL (MVP Core) ===
    path('', views.AlumnoListView.as_view(), name='alumno_list'),
    path('crear/', views.AlumnoCreateView.as_view(), name='alumno_create'),
    path('<int:pk>/', views.AlumnoDetailView.as_view(), name='alumno_detail'),
    path('<int:pk>/editar/', views.AlumnoUpdateView.as_view(), name='alumno_update'),
    path('<int:pk>/eliminar/', views.AlumnoDeleteView.as_view(), name='alumno_delete'),
    
    # === MEJORAS UX ESTRATÉGICAS (Impacto Alto, Complejidad Baja) ===
    
    # Dashboard con estadísticas - Mejora navegación
    path('dashboard/', views.StudentsIndexView.as_view(), name='dashboard'),
    
    # Búsqueda AJAX - Mejora drasticamente UX sin complejidad
    path('api/buscar/', views.AlumnoSearchAjaxView.as_view(), name='api_search'),
    
]

# === FUTURAS EXPANSIONES ===
# Estas URLs se pueden agregar incrementalmente según necesidad:
# 
# NIVEL 2 - Productividad:
# - Importar/Exportar CSV  
# - Duplicar alumno
# - Filtros avanzados
#
# NIVEL 3 - Administración: 
# - Acciones masivas
# - Reportes detallados
# - Auditoría y logs
#
# NIVEL 4 - Integración:
# - APIs REST completas
# - Webhooks
# - Sincronización
