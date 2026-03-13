from django.contrib import admin
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("apellidos", "nombres", "cedula", "sucursal", "activo")
    search_fields = ("nombres", "apellidos", "cedula")
    list_filter = ("activo", "sucursal")
