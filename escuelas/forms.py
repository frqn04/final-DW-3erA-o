from django import forms
from .models import Materia


class MateriaForm(forms.ModelForm):
    """
    Formulario para Materia con código opcional (se genera automáticamente si no se proporciona).
    """
    codigo = forms.CharField(
        max_length=20,
        required=False,
        help_text='Opcional: Se generará automáticamente si se deja vacío (ej: ABC1234)'
    )
    
    class Meta:
        model = Materia
        fields = ['carrera', 'nombre', 'codigo', 'año_carrera', 'cupo_maximo', 'descripcion', 'activa']
