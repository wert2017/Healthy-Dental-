from django.urls import path
from .views import (
    lista_pacientes,
    crear_paciente_view,
    modulo_fotos_view,
    fotos_paciente_detalle_view,
    eliminar_foto_view,
)

urlpatterns = [
    path("lista/", lista_pacientes, name="lista_pacientes"),
    path("crear/", crear_paciente_view, name="crear_paciente"),
    # Módulo de Fotografía Clínica
    path("fotos/", modulo_fotos_view, name="modulo_fotos"),
    path("<int:paciente_id>/fotos/", fotos_paciente_detalle_view, name="fotos_paciente"),
    path("fotos/<int:foto_id>/eliminar/", eliminar_foto_view, name="eliminar_foto_paciente"),
]

