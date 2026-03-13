from django import forms
from .models import Paciente

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'tipo_identificacion',
            'numero_identificacion',
            'nombres',
            'apellidos',
            'razon_social',
            'telefono',
            'email',
            'historia_clinica',
        ]
