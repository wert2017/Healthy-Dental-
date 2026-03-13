from django.db import models

class Paciente(models.Model):

    TIPO_IDENTIFICACION_CHOICES = [
        ('CED', 'Cédula'),
        ('RUC', 'RUC'),
    ]

    # Identificación
    tipo_identificacion = models.CharField(
        max_length=3,
        choices=TIPO_IDENTIFICACION_CHOICES
    )

    numero_identificacion = models.CharField(
        max_length=13,
        unique=True,
        verbose_name="Cédula / RUC"
    )

    # Persona natural
    nombres = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    apellidos = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # Persona jurídica
    razon_social = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    # Clínica
    historia_clinica = models.CharField(
        max_length=20,
        unique=True
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['historia_clinica']
        verbose_name = "Paciente / Cliente"
        verbose_name_plural = "Pacientes / Clientes"

    def __str__(self):
        return self.nombre_mostrar()

    def __str__(self):
        return self.nombre_mostrar()

    # ----------------------------
    # MÉTODOS DE APOYO
    # ----------------------------

    def es_persona_juridica(self):
        return self.tipo_identificacion == 'RUC'

    def nombre_mostrar(self):
        if self.es_persona_juridica():
            return self.razon_social
        return f"{self.nombres} {self.apellidos}".strip()
