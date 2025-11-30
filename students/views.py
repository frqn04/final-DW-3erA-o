from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Alumno
from .forms import AlumnoForm


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin que verifica que el usuario sea administrador"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()
    
    def handle_no_permission(self):
        messages.error(self.request, '⛔ Acceso denegado: Solo los administradores pueden realizar esta acción.')
        return super().handle_no_permission()


class AlumnoListView(AdminRequiredMixin, ListView):
    """Lista de alumnos - Solo administradores"""
    model = Alumno
    template_name = 'students/alumno_list.html'
    context_object_name = 'alumnos'
    paginate_by = 10


class AlumnoDetailView(AdminRequiredMixin, DetailView):
    """Detalle de un alumno - Solo administradores"""
    model = Alumno
    template_name = 'students/alumno_detail.html'
    context_object_name = 'alumno'


class AlumnoCreateView(AdminRequiredMixin, CreateView):
    """Crear nuevo alumno"""
    model = Alumno
    form_class = AlumnoForm
    template_name = 'students/alumno_form.html'
    success_url = reverse_lazy('students:alumno_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Si se creó un usuario, mostrar las credenciales
        if form.cleaned_data.get('crear_usuario') and self.object.user:
            messages.success(
                self.request,
                f'✅ Alumno "{self.object.get_full_name()}" creado exitosamente. '
                f'📧 Email: {self.object.user.email} | 🔑 Contraseña: {self.object.dni}'
            )
        else:
            messages.success(self.request, f'✅ Alumno "{self.object.get_full_name()}" creado exitosamente.')
        
        return response


class AlumnoUpdateView(AdminRequiredMixin, UpdateView):
    """Editar alumno existente"""
    model = Alumno
    form_class = AlumnoForm
    template_name = 'students/alumno_form.html'
    success_url = reverse_lazy('students:alumno_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Alumno "{form.instance.get_full_name()}" actualizado exitosamente.')
        return super().form_valid(form)


class AlumnoDeleteView(AdminRequiredMixin, DeleteView):
    """Eliminar alumno"""
    model = Alumno
    template_name = 'students/alumno_confirm_delete.html'
    success_url = reverse_lazy('students:alumno_list')
    
    def form_valid(self, form):
        try:
            messages.success(self.request, f'Alumno "{self.object.get_full_name()}" eliminado exitosamente.')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Error al eliminar: {str(e)}')
            return self.form_invalid(form)
