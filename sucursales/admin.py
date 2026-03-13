from django.contrib import admin
from .models import Sucursal

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "telefono", "email", "activo")
    search_fields = ("nombre",)
    list_filter = ("activo",)
