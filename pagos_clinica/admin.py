from django.contrib import admin
from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("atencion", "forma_pago", "monto", "fecha")
    list_filter = ("forma_pago", "fecha")
    search_fields = ("atencion__paciente__apellidos",)
