from django.db import models
from doctores.models import Doctor
from tratamientos.models import Tratamiento


class ComisionTratamiento(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="comisiones"
    )
    tratamiento = models.ForeignKey(
        Tratamiento,
        on_delete=models.CASCADE,
        related_name="comisiones"
    )

    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje de comisión (ej: 40.00)"
    )

    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("doctor", "tratamiento")

    def __str__(self):
        return f"{self.doctor} - {self.tratamiento} ({self.porcentaje}%)"
