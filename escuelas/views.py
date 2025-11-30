from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django_filters.views import FilterView
from .models import Carrera, Materia
from .filters import MateriaFilter
from .forms import MateriaForm


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin que verifica que el usuario sea administrador"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()
    
    def handle_no_permission(self):
        messages.error(self.request, '⛔ Acceso denegado: Solo los administradores pueden realizar esta acción.')
        return super().handle_no_permission()


# ====== CARRERAS ======

class CarreraListView(ListView):
    """Lista de carreras - Acceso público"""
    model = Carrera
    template_name = 'escuelas/carrera_list.html'
    context_object_name = 'carreras'
    paginate_by = 10


class CarreraDetailView(DetailView):
    """Detalle de una carrera - Acceso público"""
    model = Carrera
    template_name = 'escuelas/carrera_detail.html'
    context_object_name = 'carrera'


class CarreraCreateView(AdminRequiredMixin, CreateView):
    """Crear nueva carrera"""
    model = Carrera
    template_name = 'escuelas/carrera_form.html'
    fields = ['codigo', 'nombre', 'duracion_años', 'descripcion', 'activa']
    success_url = reverse_lazy('escuelas:carrera_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Carrera "{form.instance.nombre}" creada exitosamente.')
        return super().form_valid(form)


class CarreraUpdateView(AdminRequiredMixin, UpdateView):
    """Editar carrera existente"""
    model = Carrera
    template_name = 'escuelas/carrera_form.html'
    fields = ['codigo', 'nombre', 'duracion_años', 'descripcion', 'activa']
    success_url = reverse_lazy('escuelas:carrera_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Carrera "{form.instance.nombre}" actualizada exitosamente.')
        return super().form_valid(form)


class CarreraDeleteView(AdminRequiredMixin, DeleteView):
    """Eliminar carrera"""
    model = Carrera
    template_name = 'escuelas/carrera_confirm_delete.html'
    success_url = reverse_lazy('escuelas:carrera_list')
    
    def form_valid(self, form):
        try:
            self.object.delete()
            messages.success(self.request, f'Carrera "{self.object.nombre}" eliminada exitosamente.')
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f'Error al eliminar: {str(e)}')
            return redirect('escuelas:carrera_list')


# ====== MATERIAS ======

class MateriaListView(FilterView):
    """Lista de materias con filtros - Acceso público"""
    model = Materia
    template_name = 'escuelas/materia_list.html'
    context_object_name = 'materias'
    filterset_class = MateriaFilter
    paginate_by = 10
    
    def get_queryset(self):
        """
        Los alumnos autenticados solo ven materias de su carrera.
        Los usuarios no autenticados y admins ven todas.
        """
        queryset = super().get_queryset()
        
        if self.request.user.is_authenticated and self.request.user.is_alumno():
            # Filtrar solo las materias de la carrera del alumno
            try:
                from students.models import Alumno
                alumno = Alumno.objects.get(user=self.request.user)
                queryset = queryset.filter(carrera=alumno.carrera)
            except Alumno.DoesNotExist:
                queryset = queryset.none()
        
        return queryset.select_related('carrera')


class MateriaDetailView(DetailView):
    """Detalle de una materia - Acceso público"""
    model = Materia
    template_name = 'escuelas/materia_detail.html'
    context_object_name = 'materia'
    
    def get_queryset(self):
        """
        Los alumnos autenticados solo pueden ver detalles de materias de su carrera.
        Los usuarios no autenticados y admins pueden ver todas.
        """
        queryset = super().get_queryset()
        
        if self.request.user.is_authenticated and self.request.user.is_alumno():
            try:
                from students.models import Alumno
                alumno = Alumno.objects.get(user=self.request.user)
                queryset = queryset.filter(carrera=alumno.carrera)
            except Alumno.DoesNotExist:
                queryset = queryset.none()
        
        return queryset


class MateriaCreateView(AdminRequiredMixin, CreateView):
    """Crear nueva materia"""
    model = Materia
    form_class = MateriaForm
    template_name = 'escuelas/materia_form.html'
    success_url = reverse_lazy('escuelas:materia_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Materia "{form.instance.nombre}" creada exitosamente.')
        return super().form_valid(form)


class MateriaUpdateView(AdminRequiredMixin, UpdateView):
    """Editar materia existente"""
    model = Materia
    form_class = MateriaForm
    template_name = 'escuelas/materia_form.html'
    success_url = reverse_lazy('escuelas:materia_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Materia "{form.instance.nombre}" actualizada exitosamente.')
        return super().form_valid(form)


class MateriaDeleteView(AdminRequiredMixin, DeleteView):
    """Eliminar materia"""
    model = Materia
    template_name = 'escuelas/materia_confirm_delete.html'
    success_url = reverse_lazy('escuelas:materia_list')
    
    def form_valid(self, form):
        try:
            self.object.delete()
            messages.success(self.request, f'Materia "{self.object.nombre}" eliminada exitosamente.')
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f'Error al eliminar: {str(e)}')
            return redirect('escuelas:materia_list')
