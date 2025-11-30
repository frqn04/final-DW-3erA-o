from django import forms
from .models import Inscripcion
from students.models import Alumno


class InscripcionForm(forms.ModelForm):
    """Formulario para inscripciones"""
    
    class Meta:
        model = Inscripcion
        fields = ['alumno', 'materia', 'estado', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.alumno_actual = None
        super().__init__(*args, **kwargs)
        
        # Si el usuario es alumno, solo puede inscribirse a sí mismo
        if self.user and self.user.is_alumno():
            try:
                # Buscar el alumno asociado al usuario
                self.alumno_actual = Alumno.objects.get(user=self.user)
                
                # Remover el campo alumno completamente para alumnos
                self.fields.pop('alumno')
                
                # Filtrar materias solo de su carrera y que estén activas
                from escuelas.models import Materia
                self.fields['materia'].queryset = Materia.objects.filter(
                    carrera=self.alumno_actual.carrera,
                    activa=True
                ).order_by('año_carrera', 'nombre')
                
                # Remover el campo estado para alumnos
                self.fields.pop('estado')
                
            except Alumno.DoesNotExist:
                # Si el usuario no tiene alumno asociado, no puede inscribirse
                from escuelas.models import Materia
                self.fields['alumno'].queryset = Alumno.objects.none()
                self.fields['materia'].queryset = Materia.objects.none()
        else:
            # Si es admin, mostrar todas las materias activas
            from escuelas.models import Materia
            self.fields['materia'].queryset = Materia.objects.filter(
                activa=True
            ).select_related('carrera').order_by('carrera__nombre', 'año_carrera', 'nombre')
    
    def save(self, commit=True):
        """Asignar el alumno automáticamente si es un usuario alumno"""
        inscripcion = super().save(commit=False)
        
        # Si el usuario es alumno, asignar su registro de alumno y estado
        if self.user and self.user.is_alumno() and self.alumno_actual:
            inscripcion.alumno = self.alumno_actual
            inscripcion.estado = 'CURSANDO'
        
        if commit:
            inscripcion.save()
        
        return inscripcion
