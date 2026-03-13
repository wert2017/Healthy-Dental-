from django.db import models
from atenciones.models import Atencion


class Pago(models.Model):
    FORMA_PAGO_CHOICES = [
        ("EF", "Efectivo"),
        ("TR", "Transferencia"),
        ("TC", "Tarjeta"),
        ("AB", "Abono"),
    ]

    atencion = models.ForeignKey(
        Atencion,
        on_delete=models.CASCADE,
        related_name="pagos"
    )

    fecha = models.DateTimeField(auto_now_add=True)

    forma_pago = models.CharField(
        max_length=2,
        choices=FORMA_PAGO_CHOICES
    )

    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    referencia = models.CharField(
        max_length=100,
        blank=True,
        help_text="Referencia de transferencia o voucher"
    )

    def __str__(self):
        return f"{self.get_forma_pago_display()} - ${self.monto}"
