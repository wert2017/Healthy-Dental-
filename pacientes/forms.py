from django import forms
from .models import Paciente, FotoPaciente

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

class FotoPacienteForm(forms.ModelForm):
    class Meta:
        model = FotoPaciente
        fields = ['imagen', 'categoria', 'etapa', 'fecha_toma', 'notas']
        widgets = {
            'imagen': forms.FileInput(attrs={'class': 'form-control-file', 'id': 'input-imagen'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'etapa': forms.Select(attrs={'class': 'form-control'}),
            'fecha_toma': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ej. Avance en alineación de caninos...'}),
        }

