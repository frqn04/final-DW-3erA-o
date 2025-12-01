from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Inscripcion
from .forms import InscripcionForm


class AdminOrAlumnoMixin(UserPassesTestMixin):
    """Mixin que verifica que el usuario sea admin o alumno"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_admin() or self.request.user.is_alumno()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, '⛔ Acceso denegado: Debes ser alumno o administrador para realizar esta acción.')
        return super().handle_no_permission()


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin que verifica que el usuario sea administrador"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()
    
    def handle_no_permission(self):
        messages.error(self.request, '⛔ Acceso denegado: Solo los administradores pueden realizar esta acción.')
        return super().handle_no_permission()


class InscripcionListView(LoginRequiredMixin, ListView):
    """Lista de inscripciones"""
    model = Inscripcion
    template_name = 'enrollments/inscripcion_list.html'
    context_object_name = 'inscripciones'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Los alumnos solo ven sus propias inscripciones.
        Los admins ven todas.
        """
        queryset = super().get_queryset()
        
        if self.request.user.is_alumno():
            # Filtrar solo las inscripciones del alumno actual
            try:
                from students.models import Alumno
                alumno = Alumno.objects.get(user=self.request.user)
                queryset = queryset.filter(alumno=alumno)
            except Alumno.DoesNotExist:
                queryset = queryset.none()
        
        return queryset.select_related('alumno', 'materia', 'materia__carrera')


class InscripcionDetailView(LoginRequiredMixin, DetailView):
    """Detalle de una inscripción"""
    model = Inscripcion
    template_name = 'enrollments/inscripcion_detail.html'
    context_object_name = 'inscripcion'
    
    def get_queryset(self):
        """
        Los alumnos solo pueden ver sus propias inscripciones.
        Los admins pueden ver todas.
        """
        queryset = super().get_queryset()
        
        if self.request.user.is_alumno():
            try:
                from students.models import Alumno
                alumno = Alumno.objects.get(user=self.request.user)
                queryset = queryset.filter(alumno=alumno)
            except Alumno.DoesNotExist:
                queryset = queryset.none()
        
        return queryset


class InscripcionCreateView(AdminOrAlumnoMixin, CreateView):
    """Crear nueva inscripción"""
    model = Inscripcion
    form_class = InscripcionForm
    template_name = 'enrollments/inscripcion_form.html'
    success_url = reverse_lazy('enrollments:inscripcion_list')
    
    def get_form_kwargs(self):
        """Pasar el usuario al formulario"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            messages.success(self.request, f'Inscripción creada exitosamente.')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Error al crear inscripción: {str(e)}')
            return self.form_invalid(form)


class InscripcionUpdateView(AdminRequiredMixin, UpdateView):
    """Editar inscripción existente"""
    model = Inscripcion
    template_name = 'enrollments/inscripcion_form.html'
    fields = ['alumno', 'materia', 'estado', 'observaciones']
    success_url = reverse_lazy('enrollments:inscripcion_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Inscripción actualizada exitosamente.')
        return super().form_valid(form)


class InscripcionDeleteView(AdminOrAlumnoMixin, DeleteView):
    """Eliminar inscripción (darse de baja)"""
    model = Inscripcion
    template_name = 'enrollments/inscripcion_confirm_delete.html'
    success_url = reverse_lazy('enrollments:inscripcion_list')
    
    def get_queryset(self):
        """
        Los alumnos solo pueden eliminar sus propias inscripciones.
        Los admins pueden eliminar cualquiera.
        """
        queryset = super().get_queryset()
        
        if self.request.user.is_alumno():
            try:
                from students.models import Alumno
                alumno = Alumno.objects.get(user=self.request.user)
                queryset = queryset.filter(alumno=alumno)
            except Alumno.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    def form_valid(self, form):
        try:
            inscripcion = self.get_object()
            if self.request.user.is_alumno():
                messages.success(self.request, f'✅ Te diste de baja de "{inscripcion.materia.nombre}" exitosamente.')
            else:
                messages.success(self.request, f'✅ Inscripción eliminada exitosamente.')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'⚠️ Error al eliminar: {str(e)}')
            return self.form_invalid(form)
