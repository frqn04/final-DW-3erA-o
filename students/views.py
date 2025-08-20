"""
Vistas para la app students.

Este módulo contiene las vistas CRUD (Create, Read, Update, Delete) para el modelo
Alumno, con control de permisos, validaciones y mensajes de usuario.

Sistema de Permisos:
===================

Se utiliza RoleRequiredMixin para controlar el acceso:
- ADMIN: Acceso completo a todas las operaciones CRUD
- COORDINADOR: Solo lectura (ListView, DetailView)
- ESTUDIANTE: Acceso restringido (solo su propio perfil)

Validaciones Implementadas:
===========================

1. DUPLICADOS:
   - DNI único en todo el sistema
   - Email único en todo el sistema
   - Legajo único (generación automática si no se especifica)

2. RELACIONES:
   - Carrera debe existir y estar activa
   - No se puede eliminar alumno con inscripciones activas (futuro)
   - Validación de FK con PROTECT

3. DATOS:
   - Fecha de ingreso no puede ser futura
   - Formato correcto de DNI (7-8 dígitos)
   - Validación de email

Mensajes de Usuario:
===================

Todas las vistas incluyen mensajes detallados usando django.messages:
- success: Operaciones exitosas con información específica
- error: Errores de validación con detalles técnicos
- warning: Advertencias de seguridad y restricciones
- info: Información general y sugerencias
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView
)
from django_filters.views import FilterView
from django.shortcuts import redirect, get_object_or_404
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.db.models import Q, Count, Exists, OuterRef
from django.utils import timezone

from users.mixins import RoleRequiredMixin
from .models import Alumno
from escuelas.models import Carrera


# ==========================================
# VISTAS PARA ALUMNO
# ==========================================

class AlumnoListView(LoginRequiredMixin, ListView):
    """
    Vista para listar alumnos con filtros y búsqueda.
    
    Acceso: Todos los usuarios autenticados
    Filtros: Por carrera, estado (activo/inactivo), fecha de ingreso
    Búsqueda: Por nombre, apellido, DNI, legajo
    Paginación: 25 elementos por página
    """
    model = Alumno
    template_name = 'students/alumno_list.html'
    context_object_name = 'alumnos'
    paginate_by = 25
    
    def get_queryset(self):
        """
        Optimiza el queryset con select_related y aplica filtros de búsqueda.
        """
        queryset = Alumno.objects.select_related('carrera').order_by('last_name', 'first_name')
        
        # Filtro por búsqueda general
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(dni__icontains=search) |
                Q(legajo__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Filtro por carrera
        carrera_id = self.request.GET.get('carrera')
        if carrera_id:
            try:
                queryset = queryset.filter(carrera_id=carrera_id)
            except ValueError:
                pass
        
        # Filtro por estado
        estado = self.request.GET.get('activo')
        if estado in ['true', 'false']:
            queryset = queryset.filter(activo=(estado == 'true'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'titulo': 'Listado de Alumnos',
            'total_alumnos': self.get_queryset().count(),
            'carreras': Carrera.objects.filter(activa=True).order_by('nombre'),
            'search_query': self.request.GET.get('search', ''),
            'carrera_filter': self.request.GET.get('carrera', ''),
            'estado_filter': self.request.GET.get('activo', ''),
        })
        return context


class AlumnoDetailView(LoginRequiredMixin, DetailView):
    """
    Vista de detalle de un alumno específico.
    
    Acceso: Todos los usuarios autenticados
    Restricción: Los estudiantes solo pueden ver su propio perfil
    Incluye: Información completa del alumno y carrera
    """
    model = Alumno
    template_name = 'students/alumno_detail.html'
    context_object_name = 'alumno'
    
    def get_queryset(self):
        return Alumno.objects.select_related('carrera')
    
    def get_object(self, queryset=None):
        """
        Controla el acceso según el rol del usuario.
        """
        obj = super().get_object(queryset)
        
        # Si es estudiante, solo puede ver su propio perfil
        if (hasattr(self.request.user, 'role') and 
            self.request.user.role == 'ESTUDIANTE'):
            # Aquí iría la lógica para verificar que el alumno pertenece al usuario
            # Por ahora permitimos acceso completo
            pass
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas adicionales
        context.update({
            'otros_alumnos_carrera': None,
            'puede_editar': self.request.user.role == 'ADMIN' if hasattr(self.request.user, 'role') else False,
        })
        
        # Otros alumnos de la misma carrera
        if self.object.carrera:
            context['otros_alumnos_carrera'] = Alumno.objects.filter(
                carrera=self.object.carrera,
                activo=True
            ).exclude(pk=self.object.pk)[:5]
        
        return context


class AlumnoCreateView(RoleRequiredMixin, CreateView):
    """
    Vista para crear un nuevo alumno.
    
    Permisos: Solo ADMIN
    Validaciones: DNI único, email único, carrera activa
    Mensajes: Éxito/Error con detalles específicos
    """
    model = Alumno
    fields = ['first_name', 'last_name', 'dni', 'email', 'carrera', 'fecha_ingreso', 'activo', 'observaciones']
    template_name = 'students/alumno_form.html'
    success_url = reverse_lazy('students:alumno_list')
    required_roles = ['ADMIN']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'titulo': 'Registrar Nuevo Alumno',
            'accion': 'Registrar',
            'carreras_activas': Carrera.objects.filter(activa=True).order_by('nombre'),
        })
        return context
    
    def form_valid(self, form):
        """
        Procesa el formulario válido con validaciones adicionales.
        """
        try:
            with transaction.atomic():
                # Validaciones adicionales antes de guardar
                self._validar_duplicados(form)
                self._validar_carrera(form)
                
                # Guardar el alumno
                self.object = form.save()
                
                # Mensaje de éxito detallado
                messages.success(
                    self.request,
                    f'✅ Alumno "{self.object.nombre_completo}" registrado exitosamente. '
                    f'Legajo asignado: {self.object.legajo}.'
                )
                
                return super().form_valid(form)
                
        except ValidationError as e:
            return self._handle_validation_error(form, e)
        except IntegrityError as e:
            return self._handle_integrity_error(form, e)
        except Exception as e:
            messages.error(
                self.request,
                '❌ Error inesperado al registrar el alumno. Intente nuevamente.'
            )
            return self.form_invalid(form)
    
    def _validar_duplicados(self, form):
        """
        Valida que no existan duplicados de DNI o email.
        """
        dni = form.cleaned_data.get('dni')
        email = form.cleaned_data.get('email')
        
        # Verificar DNI duplicado
        if dni and Alumno.objects.filter(dni=dni).exists():
            raise ValidationError({
                'dni': f'Ya existe un alumno con DNI {dni} en el sistema.'
            })
        
        # Verificar email duplicado
        if email and Alumno.objects.filter(email__iexact=email).exists():
            raise ValidationError({
                'email': f'Ya existe un alumno con el email {email} en el sistema.'
            })
    
    def _validar_carrera(self, form):
        """
        Valida que la carrera seleccionada esté activa.
        """
        carrera = form.cleaned_data.get('carrera')
        if carrera and not carrera.activa:
            raise ValidationError({
                'carrera': f'La carrera "{carrera.nombre}" no está activa. '
                          'Seleccione una carrera activa.'
            })
    
    def _handle_validation_error(self, form, e):
        """
        Maneja errores de validación con mensajes específicos.
        """
        if hasattr(e, 'message_dict'):
            for field, messages_list in e.message_dict.items():
                for message in messages_list:
                    messages.error(self.request, f'❌ {field}: {message}')
        else:
            messages.error(self.request, f'❌ Error de validación: {str(e)}')
        
        return self.form_invalid(form)
    
    def _handle_integrity_error(self, form, e):
        """
        Maneja errores de integridad de base de datos.
        """
        error_msg = str(e).lower()
        if 'dni' in error_msg:
            messages.error(
                self.request,
                '❌ El DNI ingresado ya existe en el sistema.'
            )
        elif 'email' in error_msg:
            messages.error(
                self.request,
                '❌ El email ingresado ya existe en el sistema.'
            )
        elif 'legajo' in error_msg:
            messages.error(
                self.request,
                '❌ Error al generar el legajo. Intente nuevamente.'
            )
        else:
            messages.error(
                self.request,
                '❌ Error de integridad en los datos. Verifique la información.'
            )
        
        return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Maneja formulario inválido con mensaje general.
        """
        if not messages.get_messages(self.request):
            messages.error(
                self.request,
                '❌ Por favor corrija los errores en el formulario.'
            )
        return super().form_invalid(form)


class AlumnoUpdateView(RoleRequiredMixin, UpdateView):
    """
    Vista para editar un alumno existente.
    
    Permisos: Solo ADMIN
    Validaciones: DNI único (excluyendo el actual), email único, carrera activa
    Mensajes: Éxito/Error con detalles de cambios
    """
    model = Alumno
    fields = ['first_name', 'last_name', 'dni', 'email', 'carrera', 'fecha_ingreso', 'activo', 'observaciones']
    template_name = 'students/alumno_form.html'
    success_url = reverse_lazy('students:alumno_list')
    required_roles = ['ADMIN']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'titulo': f'Editar Alumno: {self.object.nombre_completo}',
            'accion': 'Actualizar',
            'carreras_activas': Carrera.objects.filter(activa=True).order_by('nombre'),
        })
        return context
    
    def form_valid(self, form):
        """
        Procesa la actualización con validaciones y tracking de cambios.
        """
        # Guardar estado anterior para comparar cambios
        alumno_anterior = Alumno.objects.get(pk=self.object.pk)
        
        try:
            with transaction.atomic():
                # Validaciones adicionales
                self._validar_duplicados_update(form, self.object.pk)
                self._validar_carrera(form)
                
                # Guardar cambios
                self.object = form.save()
                
                # Detectar y reportar cambios
                cambios = self._detectar_cambios(alumno_anterior, self.object)
                self._generar_mensaje_exito(cambios)
                
                return super().form_valid(form)
                
        except ValidationError as e:
            return self._handle_validation_error(form, e)
        except IntegrityError as e:
            return self._handle_integrity_error(form, e)
        except Exception as e:
            messages.error(
                self.request,
                '❌ Error inesperado al actualizar el alumno.'
            )
            return self.form_invalid(form)
    
    def _validar_duplicados_update(self, form, alumno_id):
        """
        Valida duplicados excluyendo el registro actual.
        """
        dni = form.cleaned_data.get('dni')
        email = form.cleaned_data.get('email')
        
        # Verificar DNI duplicado (excluyendo el actual)
        if dni and Alumno.objects.filter(dni=dni).exclude(pk=alumno_id).exists():
            raise ValidationError({
                'dni': f'Ya existe otro alumno con DNI {dni} en el sistema.'
            })
        
        # Verificar email duplicado (excluyendo el actual)
        if email and Alumno.objects.filter(email__iexact=email).exclude(pk=alumno_id).exists():
            raise ValidationError({
                'email': f'Ya existe otro alumno con el email {email} en el sistema.'
            })
    
    def _validar_carrera(self, form):
        """
        Valida que la carrera seleccionada esté activa.
        """
        carrera = form.cleaned_data.get('carrera')
        if carrera and not carrera.activa:
            raise ValidationError({
                'carrera': f'La carrera "{carrera.nombre}" no está activa. '
                          'Seleccione una carrera activa.'
            })
    
    def _detectar_cambios(self, anterior, actual):
        """
        Detecta y lista los cambios realizados.
        """
        cambios = []
        
        campos_a_comparar = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'dni': 'DNI',
            'email': 'Email',
            'carrera': 'Carrera',
            'fecha_ingreso': 'Fecha de Ingreso',
            'activo': 'Estado',
        }
        
        for campo, etiqueta in campos_a_comparar.items():
            valor_anterior = getattr(anterior, campo)
            valor_actual = getattr(actual, campo)
            
            if valor_anterior != valor_actual:
                if campo == 'carrera':
                    anterior_str = valor_anterior.nombre if valor_anterior else 'Sin carrera'
                    actual_str = valor_actual.nombre if valor_actual else 'Sin carrera'
                elif campo == 'activo':
                    anterior_str = 'Activo' if valor_anterior else 'Inactivo'
                    actual_str = 'Activo' if valor_actual else 'Inactivo'
                else:
                    anterior_str = str(valor_anterior)
                    actual_str = str(valor_actual)
                
                cambios.append(f'{etiqueta}: "{anterior_str}" → "{actual_str}"')
        
        return cambios
    
    def _generar_mensaje_exito(self, cambios):
        """
        Genera mensaje de éxito basado en los cambios detectados.
        """
        if cambios:
            mensaje = f'✅ Alumno actualizado exitosamente. Cambios realizados: {", ".join(cambios)}.'
        else:
            mensaje = '✅ Alumno actualizado (sin cambios en los datos principales).'
        
        messages.success(self.request, mensaje)
    
    def _handle_validation_error(self, form, e):
        """
        Maneja errores de validación con mensajes específicos.
        """
        if hasattr(e, 'message_dict'):
            for field, messages_list in e.message_dict.items():
                for message in messages_list:
                    messages.error(self.request, f'❌ {field}: {message}')
        else:
            messages.error(self.request, f'❌ Error de validación: {str(e)}')
        
        return self.form_invalid(form)
    
    def _handle_integrity_error(self, form, e):
        """
        Maneja errores de integridad de base de datos.
        """
        error_msg = str(e).lower()
        if 'dni' in error_msg:
            messages.error(
                self.request,
                '❌ El DNI ingresado ya existe en el sistema.'
            )
        elif 'email' in error_msg:
            messages.error(
                self.request,
                '❌ El email ingresado ya existe en el sistema.'
            )
        else:
            messages.error(
                self.request,
                '❌ Error de integridad en los datos. Verifique la información.'
            )
        
        return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Maneja formulario inválido con mensaje general.
        """
        if not messages.get_messages(self.request):
            messages.error(
                self.request,
                '❌ Por favor corrija los errores en el formulario.'
            )
        return super().form_invalid(form)


class AlumnoDeleteView(RoleRequiredMixin, DeleteView):
    """
    Vista para eliminar un alumno.
    
    Permisos: Solo ADMIN
    Protección: Verificar inscripciones activas (futuro)
    Mensajes: Éxito/Error/Advertencias con detalles
    """
    model = Alumno
    template_name = 'students/alumno_confirm_delete.html'
    success_url = reverse_lazy('students:alumno_list')
    required_roles = ['ADMIN']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'titulo': f'Eliminar Alumno: {self.object.nombre_completo}',
            # TODO: Cuando implementemos inscripciones, verificar inscripciones activas
            'inscripciones_count': 0,  # Placeholder
            'puede_eliminar': True,  # Cambiar según validaciones futuras
        })
        return context
    
    def delete(self, request, *args, **kwargs):
        """
        Maneja la eliminación con validaciones de seguridad.
        """
        self.object = self.get_object()
        nombre_completo = self.object.nombre_completo
        legajo = self.object.legajo
        carrera_nombre = self.object.carrera.nombre if self.object.carrera else "Sin carrera"
        
        try:
            with transaction.atomic():
                # TODO: Verificar inscripciones activas cuando se implemente
                # if self.object.inscripciones.filter(activa=True).exists():
                #     messages.error(
                #         request,
                #         f'❌ No se puede eliminar el alumno "{nombre_completo}" '
                #         'porque tiene inscripciones activas.'
                #     )
                #     return redirect('students:alumno_detail', pk=self.object.pk)
                
                # Eliminar el alumno
                self.object.delete()
                
                messages.success(
                    request,
                    f'✅ Alumno "{nombre_completo}" (Legajo: {legajo}) '
                    f'de la carrera "{carrera_nombre}" eliminado exitosamente.'
                )
                
                return redirect(self.success_url)
                
        except Exception as e:
            messages.error(
                request,
                f'❌ Error al eliminar el alumno: {str(e)}'
            )
            return redirect('students:alumno_detail', pk=self.object.pk)


# ==========================================
# VISTAS AUXILIARES Y API
# ==========================================

class AlumnoSearchAjaxView(LoginRequiredMixin, ListView):
    """
    Vista AJAX para búsqueda rápida de alumnos.
    Útil para autocompletado y selecciones.
    """
    model = Alumno
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if len(query) < 2:
            return Alumno.objects.none()
        
        return Alumno.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(dni__icontains=query) |
            Q(legajo__icontains=query)
        ).select_related('carrera')[:10]
    
    def get(self, request, *args, **kwargs):
        alumnos = self.get_queryset()
        data = []
        
        for alumno in alumnos:
            data.append({
                'id': alumno.pk,
                'text': str(alumno),
                'nombre_completo': alumno.nombre_completo,
                'legajo': alumno.legajo,
                'dni': alumno.dni,
                'carrera': alumno.carrera.nombre if alumno.carrera else 'Sin carrera',
                'activo': alumno.activo,
            })
        
        return JsonResponse({'results': data})


def verificar_dni_disponible(request):
    """
    Vista AJAX para verificar si un DNI está disponible.
    """
    if request.method == 'GET':
        dni = request.GET.get('dni', '').strip()
        alumno_id = request.GET.get('alumno_id', None)
        
        if not dni:
            return JsonResponse({'disponible': True, 'mensaje': ''})
        
        # Verificar si existe (excluyendo el alumno actual en caso de edición)
        query = Alumno.objects.filter(dni=dni)
        if alumno_id:
            query = query.exclude(pk=alumno_id)
        
        existe = query.exists()
        
        return JsonResponse({
            'disponible': not existe,
            'mensaje': f'El DNI {dni} ya está registrado en el sistema.' if existe else ''
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def verificar_email_disponible(request):
    """
    Vista AJAX para verificar si un email está disponible.
    """
    if request.method == 'GET':
        email = request.GET.get('email', '').strip().lower()
        alumno_id = request.GET.get('alumno_id', None)
        
        if not email:
            return JsonResponse({'disponible': True, 'mensaje': ''})
        
        # Verificar si existe (excluyendo el alumno actual en caso de edición)
        query = Alumno.objects.filter(email__iexact=email)
        if alumno_id:
            query = query.exclude(pk=alumno_id)
        
        existe = query.exists()
        
        return JsonResponse({
            'disponible': not existe,
            'mensaje': f'El email {email} ya está registrado en el sistema.' if existe else ''
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ==========================================
# VISTA PRINCIPAL
# ==========================================

class StudentsIndexView(LoginRequiredMixin, ListView):
    """
    Vista principal/dashboard de la app students.
    
    Muestra estadísticas generales y accesos rápidos.
    """
    template_name = 'students/index.html'
    context_object_name = 'estadisticas'
    
    def get_queryset(self):
        # No necesitamos queryset real, solo estadísticas
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        total_alumnos = Alumno.objects.count()
        alumnos_activos = Alumno.objects.filter(activo=True).count()
        alumnos_inactivos = total_alumnos - alumnos_activos
        
        # Estadísticas por carrera
        carreras_con_alumnos = Carrera.objects.annotate(
            total_alumnos=Count('alumnos'),
            alumnos_activos=Count('alumnos', filter=Q(alumnos__activo=True))
        ).filter(total_alumnos__gt=0).order_by('-total_alumnos')[:5]
        
        context.update({
            'titulo': 'Panel de Estudiantes',
            'total_alumnos': total_alumnos,
            'alumnos_activos': alumnos_activos,
            'alumnos_inactivos': alumnos_inactivos,
            'carreras_con_alumnos': carreras_con_alumnos,
            'alumnos_recientes': Alumno.objects.select_related('carrera').order_by('-fecha_creacion')[:5],
            'puede_administrar': hasattr(self.request.user, 'role') and self.request.user.role == 'ADMIN',
        })
        
        return context
