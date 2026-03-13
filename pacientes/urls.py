from django.urls import path
from .views import lista_pacientes, crear_paciente_view

urlpatterns = [
    path("lista/", lista_pacientes, name="lista_pacientes"),
    path("crear/", crear_paciente_view, name="crear_paciente"),
]
