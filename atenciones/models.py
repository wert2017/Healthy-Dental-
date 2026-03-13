from django.db import models
from decimal import Decimal
from pacientes.models import Paciente
from doctores.models import Doctor
from tratamientos.models import Tratamiento


class Atencion(models.Model):
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name="atenciones"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name="atenciones",
        null=True,
        blank=True
    )

    fecha = models.DateTimeField()
    observaciones = models.TextField(blank=True)

    ESTADO_CHOICES = [
        ("EN_PROCESO", "En Proceso"),
        ("FINALIZADO", "Finalizado"),
    ]

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="EN_PROCESO"
    )

    validado = models.BooleanField(default=False, help_text="Si es True, la atención está conciliada y bloqueada.")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Atención {self.id} - {self.paciente}"

    @property
    def tratamientos_str(self):
        """Devuelve los nombres de tratamientos concatenados"""
        nombres = self.detalles.values_list('tratamiento__nombre', flat=True)
        return ", ".join(nombres)

    @property
    def monto_efectivo(self):
        return self.pagos.filter(forma_pago='EF').aggregate(t=models.Sum('monto'))['t'] or Decimal("0.00")

    @property
    def monto_transferencia(self):
        return self.pagos.filter(forma_pago='TR').aggregate(t=models.Sum('monto'))['t'] or Decimal("0.00")

    @property
    def monto_tarjeta(self):
        t1 = self.pagos.filter(forma_pago='TC').aggregate(t=models.Sum('monto'))['t'] or Decimal("0.00")
        t2 = self.pagos.filter(forma_pago='TD').aggregate(t=models.Sum('monto'))['t'] or Decimal("0.00")
        return t1 + t2

    @property
    def monto_abono(self):
        return self.pagos.filter(forma_pago='AB').aggregate(t=models.Sum('monto'))['t'] or Decimal("0.00")

    @property
    def total_pagado(self):
        return self.pagos.aggregate(t=models.Sum('monto'))['t'] or Decimal("0.00")

    @property
    def total_atencion_valor(self):
        return self.detalles.aggregate(t=models.Sum('total_calculado'))['t'] or Decimal("0.00")

    @property # [NEW]
    def total_comision(self):
        """Calcula el valor total de comisiones (detalles * porcentaje)"""
        total = Decimal("0.00")
        for detalle in self.detalles.all():
            # (precio * cantidad) * (porcentaje / 100)
            subtotal = detalle.total_calculado
            comision = subtotal * (detalle.porcentaje_comision / 100)
            total += comision
        return round(total, 2)

    @property
    def saldo_cxc(self):
        # Calculamos saldo pendiente: Total Atención - Total Pagado
        # Usamos 'self.total_atencion_valor' y 'self.total_pagado' que ya son propiedades/decimales
        return self.total_atencion_valor - self.total_pagado




class AtencionDetalle(models.Model):
    atencion = models.ForeignKey(
        Atencion,
        on_delete=models.CASCADE,
        related_name="detalles"
    )

    tratamiento = models.ForeignKey(
        Tratamiento,
        on_delete=models.PROTECT
    )

    cantidad = models.PositiveIntegerField(default=1)

    precio_base = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    aplica_iva = models.BooleanField(default=False)

    porcentaje_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("12.00")
    )

    iva_calculado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    total_calculado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    porcentaje_comision = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00")
    )

    confirmado = models.BooleanField(default=False)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)

    # =========================
    # CÁLCULOS ROBUSTOS
    # =========================
    def calcular_totales(self):
        precio = Decimal(self.precio_base)
        cantidad = Decimal(self.cantidad)
        descuento = Decimal(self.descuento)

        base = (precio * cantidad) - descuento

        if base < 0:
            base = Decimal("0.00")

        if self.aplica_iva:
            self.iva_calculado = (base * Decimal(self.porcentaje_iva)) / Decimal("100")
        else:
            self.iva_calculado = Decimal("0.00")

        self.total_calculado = base + self.iva_calculado

    def monto_comision(self):
        if self.confirmado:
            base = (Decimal(self.precio_base) * Decimal(self.cantidad)) - Decimal(self.descuento)
            return base * (Decimal(self.porcentaje_comision) / Decimal("100"))
        return Decimal("0.00")

    def save(self, *args, **kwargs):
        self.calcular_totales()
        super().save(*args, **kwargs)

    def __str__(self):
        estado = "✔" if self.confirmado else "⏳"
        return f"{estado} {self.tratamiento}"
