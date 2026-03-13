from django.contrib import admin
from .models import Tratamiento

@admin.register(Tratamiento)
class TratamientoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "precio_base", "activo")
    search_fields = ("codigo", "nombre")
    list_filter = ("activo",)