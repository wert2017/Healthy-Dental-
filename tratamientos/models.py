from django.db import models


class Tratamiento(models.Model):
    codigo = models.CharField(
        max_length=20,
        help_text="Código interno del tratamiento (ej: LD-001)"
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
