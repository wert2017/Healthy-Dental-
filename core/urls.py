from django.contrib import admin
from django.urls import path, include

from django.shortcuts import redirect

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", lambda request: redirect("recepcion", permanent=True)),
    path("", include("atenciones.urls")),
    path("pacientes/", include("pacientes.urls")),
]
