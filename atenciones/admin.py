from django.contrib import admin
from django.utils import timezone
from django.db.models import Sum, F, DecimalField, ExpressionWrapper

from .models import Atencion, AtencionDetalle
from pagos_clinica.models import Pago


class AtencionDetalleInline(admin.TabularInline):
    model = AtencionDetalle
    extra = 0


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 1


@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    # =========================
    # LISTA DE ATENCIONES
    # =========================
    list_display = (
        "id",
        "fecha",
        "paciente",
        "doctor_corto",
        "total_atencion",
        "total_pagado",
        "saldo",
        "estado",
    )

    list_filter = ("doctor",)
    date_hierarchy = "fecha"

    search_fields = (
        "paciente__apellidos",
        "paciente__nombres",
        "doctor__apellidos",
    )

    inlines = [AtencionDetalleInline, PagoInline]

    actions = ["confirmar_atencion"]

    # =========================
    # PERMISOS
    # =========================
    def has_change_permission(self, request, obj=None):
        if obj:
            return obj.detalles.filter(confirmado=False).exists()
        return True

    # =========================
    # COLUMNAS
    # =========================
    def doctor_corto(self, obj):
        return obj.doctor.apellidos if obj.doctor else "---"

    doctor_corto.short_description = "Doctor"

    def estado(self, obj):
        pendientes = obj.detalles.filter(confirmado=False).exists()
        return "PENDIENTE" if pendientes else "CONFIRMADA"

    estado.short_description = "Estado"

    # =========================
    # TOTALES
    # =========================
    def total_atencion(self, obj):
        total = obj.detalles.aggregate(total=Sum("total_calculado"))["total"]
        return total or 0

    total_atencion.short_description = "Total $"

    def total_pagado(self, obj):
        total = obj.pagos.aggregate(
            total=Sum("monto")
        )["total"]
        return total or 0

    total_pagado.short_description = "Pagado $"

    def saldo(self, obj):
        return self.total_atencion(obj) - self.total_pagado(obj)

    saldo.short_description = "Saldo (CXC)"

    # =========================
    # ACCIÓN CONFIRMAR
    # =========================
    def confirmar_atencion(self, request, queryset):
        for atencion in queryset:
            for detalle in atencion.detalles.filter(confirmado=False):
                detalle.confirmado = True
                detalle.fecha_confirmacion = timezone.now()
                detalle.save()

        self.message_user(
            request,
            "Atención confirmada correctamente (con aprobación del doctor)."
        )

    confirmar_atencion.short_description = (
        "Confirmar atención (con aprobación del doctor)"
    )
