"""
Vistas para la app escuelas.

Este módulo contiene las vistas CRUD (Create, Read, Update, Delete) para los modelos
Carrera y Materia, con control de permisos y mensajes de usuario.

Sistema de Permisos:
===================

Se utiliza RoleRequiredMixin para controlar el acceso:
- ADMIN: Acceso completo a todas las operaciones CRUD
- COORDINADOR: Solo lectura (ListView)
- ESTUDIANTE: Solo lectura de materias públicas

Mensajes de Usuario:
===================

Todas las vistas incluyen mensajes de éxito/error usando django.messages:
- success: Operaciones exitosas (crear, actualizar, eliminar)
- error: Errores de validación o permisos
- warning: Advertencias de seguridad
- info: Información general
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView
)
from django_filters.views import FilterView
from django.shortcuts import redirect
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import Http404

from users.mixins import RoleRequiredMixin
from .models import Carrera, Materia
from .filters import MateriaFilter, CarreraFilter
from .forms import CarreraForm, MateriaForm


# ==========================================
# VISTAS PARA CARRERA
# ==========================================

class CarreraListView(LoginRequiredMixin, FilterView):
    """
    Vista para listar carreras con filtros.
    
    Acceso: Todos los usuarios autenticados
    Filtros: Por nombre
    Paginación: 20 elementos por página
    """
    model = Carrera
    filterset_class = CarreraFilter
    template_name = 'escuelas/carrera_list.html'
    context_object_name = 'carreras'
    paginate_by = 20
    
    def get_queryset(self):
        """Optimiza el queryset base"""
        return Carrera.objects.all().order_by('nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_carreras'] = self.get_queryset().count()
        context['titulo'] = 'Listado de Carreras'
        return context


class CarreraDetailView(LoginRequiredMixin, DetailView):
    """
    Vista de detalle de una carrera específica.
    
    Acceso: Todos los usuarios autenticados
    Incluye: Lista de materias de la carrera
    """
    model = Carrera
    template_name = 'escuelas/carrera_detail.html'
    context_object_name = 'carrera'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Incluir materias de la carrera
        context['materias'] = self.object.materias.all().order_by('nombre')
        context['total_materias'] = context['materias'].count()
        return context


class CarreraCreateView(RoleRequiredMixin, CreateView):
    """
    Vista para crear una nueva carrera.
    
    Permisos: Solo ADMIN
    Validaciones: Nombre único
    Mensajes: Éxito/Error
    """
    model = Carrera
    form_class = CarreraForm
    template_name = 'escuelas/carrera_form.html'
    success_url = reverse_lazy('escuelas:carrera_list')
    required_roles = ['ADMIN']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nueva Carrera'
        context['accion'] = 'Crear'
        context['carreras'] = Carrera.objects.all().order_by('nombre')
        return context
    
    def form_valid(self, form):
        """
        Procesa el formulario válido con mensajes de éxito.
        """
        try:
            with transaction.atomic():
                # Guardar la carrera
                self.object = form.save()
                
                # Mensaje de éxito
                messages.success(
                    self.request,
                    f'✅ Carrera "{self.object.nombre}" creada exitosamente.'
                )
                
                return super().form_valid(form)
                
        except ValidationError as e:
            # Error de validación
            messages.error(
                self.request,
                f'❌ Error al crear la carrera: {str(e)}'
            )
            return self.form_invalid(form)
        except Exception as e:
            # Error inesperado
            messages.error(
                self.request,
                '❌ Error inesperado al crear la carrera. Intente nuevamente.'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Maneja formulario inválido con mensajes de error.
        """
        messages.error(
            self.request,
            '❌ Por favor corrija los errores en el formulario.'
        )
        return super().form_invalid(form)


class CarreraUpdateView(RoleRequiredMixin, UpdateView):
    """
    Vista para editar una carrera existente.
    
    Permisos: Solo ADMIN
    Validaciones: Nombre único
    Mensajes: Éxito/Error
    """
    model = Carrera
    form_class = CarreraForm
    template_name = 'escuelas/carrera_form.html'
    success_url = reverse_lazy('escuelas:carrera_list')
    required_roles = ['ADMIN']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Carrera: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        context['carreras'] = Carrera.objects.all().order_by('nombre')
        return context
    
    def form_valid(self, form):
        """
        Procesa la actualización con mensajes de éxito.
        """
        nombre_anterior = self.object.nombre
        
        try:
            with transaction.atomic():
                self.object = form.save()
                
                messages.success(
                    self.request,
                    f'✅ Carrera actualizada de "{nombre_anterior}" a "{self.object.nombre}".'
                )
                
                return super().form_valid(form)
                
        except ValidationError as e:
            messages.error(
                self.request,
                f'❌ Error al actualizar la carrera: {str(e)}'
            )
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request,
                '❌ Error inesperado al actualizar la carrera.'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Por favor corrija los errores en el formulario.'
        )
        return super().form_invalid(form)


class CarreraDeleteView(RoleRequiredMixin, DeleteView):
    """
    Vista para eliminar una carrera.
    
    Permisos: Solo ADMIN
    Protección: No permite eliminar si tiene materias (PROTECT)
    Mensajes: Éxito/Error/Advertencias
    """
    model = Carrera
    template_name = 'escuelas/carrera_confirm_delete.html'
    success_url = reverse_lazy('escuelas:carrera_list')
    required_roles = ['ADMIN']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Carrera: {self.object.nombre}'
        # Verificar si tiene materias asociadas
        context['materias_count'] = self.object.materias.count()
        context['materias'] = self.object.materias.all()[:5]  # Mostrar las primeras 5
        return context
    
    def delete(self, request, *args, **kwargs):
        """
        Maneja la eliminación con validaciones de PROTECT.
        """
        self.object = self.get_object()
        nombre_carrera = self.object.nombre
        materias_count = self.object.materias.count()
        
        try:
            with transaction.atomic():
                # Verificar si tiene materias (por la restricción PROTECT)
                if materias_count > 0:
                    messages.error(
                        request,
                        f'❌ No se puede eliminar la carrera "{nombre_carrera}" porque tiene {materias_count} materia(s) asociada(s). '
                        f'Primero debe eliminar o reubicar las materias.'
                    )
                    return redirect('escuelas:carrera_detail', pk=self.object.pk)
                
                # Eliminar la carrera
                self.object.delete()
                
                messages.success(
                    request,
                    f'✅ Carrera "{nombre_carrera}" eliminada exitosamente.'
                )
                
                return redirect(self.success_url)
                
        except Exception as e:
            messages.error(
                request,
                f'❌ Error al eliminar la carrera: {str(e)}'
            )
            return redirect('escuelas:carrera_detail', pk=self.object.pk)


# ==========================================
# VISTAS PARA MATERIA
# ==========================================

class MateriaListView(LoginRequiredMixin, FilterView):
    """
    Vista para listar materias con filtros avanzados.
    
    Acceso: Todos los usuarios autenticados
    Filtros: Por carrera, cupo disponible, nombre
    Paginación: 20 elementos por página
    """
    model = Materia
    filterset_class = MateriaFilter
    template_name = 'escuelas/materia_list.html'
    context_object_name = 'materias'
    paginate_by = 20
    
    def get_queryset(self):
        """Optimiza el queryset con select_related"""
        return Materia.objects.select_related('carrera').order_by('carrera__nombre', 'nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_materias'] = self.get_queryset().count()
        context['titulo'] = 'Listado de Materias'
        return context


class MateriaDetailView(LoginRequiredMixin, DetailView):
    """
    Vista de detalle de una materia específica.
    
    Acceso: Todos los usuarios autenticados
    Incluye: Información completa de la materia y carrera
    """
    model = Materia
    template_name = 'escuelas/materia_detail.html'
    context_object_name = 'materia'
    
    def get_queryset(self):
        return Materia.objects.select_related('carrera')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Información adicional
        context['otras_materias'] = Materia.objects.filter(
            carrera=self.object.carrera
        ).exclude(pk=self.object.pk)[:5]
        return context


class MateriaCreateView(RoleRequiredMixin, CreateView):
    """
    Vista para crear una nueva materia.
    
    Permisos: Solo ADMIN
    Validaciones: UniqueConstraint (carrera, nombre)
    Mensajes: Éxito/Error
    """
    model = Materia
    form_class = MateriaForm
    template_name = 'escuelas/materia_form.html'
    success_url = reverse_lazy('escuelas:materia_list')
    required_roles = ['ADMIN']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nueva Materia'
        context['accion'] = 'Crear'
        context['carreras'] = Carrera.objects.all().order_by('nombre')
        return context
    
    def form_valid(self, form):
        """
        Procesa el formulario válido con validaciones adicionales.
        """
        try:
            with transaction.atomic():
                self.object = form.save()
                
                messages.success(
                    self.request,
                    f'✅ Materia "{self.object.nombre}" creada exitosamente en la carrera "{self.object.carrera.nombre}".'
                )
                
                return super().form_valid(form)
                
        except ValidationError as e:
            # Error de UniqueConstraint o validación
            if 'unique_materia_por_carrera' in str(e):
                messages.error(
                    self.request,
                    f'❌ Ya existe una materia con el nombre "{form.cleaned_data.get("nombre")}" '
                    f'en la carrera "{form.cleaned_data.get("carrera")}".'
                )
            else:
                messages.error(
                    self.request,
                    f'❌ Error de validación: {str(e)}'
                )
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request,
                '❌ Error inesperado al crear la materia. Intente nuevamente.'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Por favor corrija los errores en el formulario.'
        )
        return super().form_invalid(form)


class MateriaUpdateView(RoleRequiredMixin, UpdateView):
    """
    Vista para editar una materia existente.
    
    Permisos: Solo ADMIN
    Validaciones: UniqueConstraint (carrera, nombre)
    Mensajes: Éxito/Error
    """
    model = Materia
    form_class = MateriaForm
    template_name = 'escuelas/materia_form.html'
    success_url = reverse_lazy('escuelas:materia_list')
    required_roles = ['ADMIN']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Materia: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        context['carreras'] = Carrera.objects.all().order_by('nombre')
        return context
    
    def form_valid(self, form):
        """
        Procesa la actualización con mensajes informativos.
        """
        nombre_anterior = self.object.nombre
        carrera_anterior = self.object.carrera
        
        try:
            with transaction.atomic():
                self.object = form.save()
                
                # Mensaje detallado de cambios
                cambios = []
                if nombre_anterior != self.object.nombre:
                    cambios.append(f'nombre: "{nombre_anterior}" → "{self.object.nombre}"')
                if carrera_anterior != self.object.carrera:
                    cambios.append(f'carrera: "{carrera_anterior}" → "{self.object.carrera}"')
                
                if cambios:
                    mensaje = f'✅ Materia actualizada. Cambios: {", ".join(cambios)}.'
                else:
                    mensaje = '✅ Materia actualizada exitosamente.'
                
                messages.success(self.request, mensaje)
                
                return super().form_valid(form)
                
        except ValidationError as e:
            if 'unique_materia_por_carrera' in str(e):
                messages.error(
                    self.request,
                    f'❌ Ya existe una materia con el nombre "{form.cleaned_data.get("nombre")}" '
                    f'en la carrera "{form.cleaned_data.get("carrera")}".'
                )
            else:
                messages.error(
                    self.request,
                    f'❌ Error de validación: {str(e)}'
                )
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request,
                '❌ Error inesperado al actualizar la materia.'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Por favor corrija los errores en el formulario.'
        )
        return super().form_invalid(form)


class MateriaDeleteView(RoleRequiredMixin, DeleteView):
    """
    Vista para eliminar una materia.
    
    Permisos: Solo ADMIN
    Protección: Verificar inscripciones activas (cuando se implemente)
    Mensajes: Éxito/Error/Advertencias
    """
    model = Materia
    template_name = 'escuelas/materia_confirm_delete.html'
    success_url = reverse_lazy('escuelas:materia_list')
    required_roles = ['ADMIN']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Materia: {self.object.nombre}'
        # TODO: Cuando implementemos inscripciones, verificar inscripciones activas
        # context['inscripciones_count'] = self.object.inscripciones.count()
        context['inscripciones_count'] = 0  # Placeholder
        return context
    
    def delete(self, request, *args, **kwargs):
        """
        Maneja la eliminación con validaciones.
        """
        self.object = self.get_object()
        nombre_materia = self.object.nombre
        carrera_nombre = self.object.carrera.nombre
        
        try:
            with transaction.atomic():
                # TODO: Verificar inscripciones activas cuando se implemente
                # if self.object.inscripciones.count() > 0:
                #     messages.error(
                #         request,
                #         f'❌ No se puede eliminar la materia "{nombre_materia}" porque tiene estudiantes inscriptos.'
                #     )
                #     return redirect('escuelas:materia_detail', pk=self.object.pk)
                
                self.object.delete()
                
                messages.success(
                    request,
                    f'✅ Materia "{nombre_materia}" de la carrera "{carrera_nombre}" eliminada exitosamente.'
                )
                
                return redirect(self.success_url)
                
        except Exception as e:
            messages.error(
                request,
                f'❌ Error al eliminar la materia: {str(e)}'
            )
            return redirect('escuelas:materia_detail', pk=self.object.pk)


# ==========================================
# VISTA PRINCIPAL
# ==========================================

class EscuelasIndexView(LoginRequiredMixin, ListView):
    """
    Vista principal/dashboard de la app escuelas.
    
    Muestra estadísticas generales y accesos rápidos.
    """
    template_name = 'escuelas/index.html'
    context_object_name = 'estadisticas'
    
    def get_queryset(self):
        # No necesitamos queryset real, solo estadísticas
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        context.update({
            'total_carreras': Carrera.objects.count(),
            'total_materias': Materia.objects.count(),
            'carreras_recientes': Carrera.objects.order_by('-fecha_creacion')[:5],
            'materias_recientes': Materia.objects.select_related('carrera').order_by('-fecha_creacion')[:5],
            'titulo': 'Panel de Escuelas',
        })
        
        return context
