from django.contrib import admin
from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):

    list_display = (
        "historia_clinica",
        "nombre_mostrar",
        "tipo_identificacion",
        "numero_identificacion",
        "telefono",
        "activo",
    )

    search_fields = (
        "historia_clinica",
        "numero_identificacion",
        "nombres",
        "apellidos",
        "razon_social",
    )

    list_filter = (
        "activo",
        "tipo_identificacion",
    )
