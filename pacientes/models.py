from django.db import models
from django.utils import timezone

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

    # ----------------------------
    # MÉTODOS DE APOYO
    # ----------------------------

    def es_persona_juridica(self):
        return self.tipo_identificacion == 'RUC'

    def nombre_mostrar(self):
        if self.es_persona_juridica():
            return self.razon_social
        return f"{self.nombres} {self.apellidos}".strip()


class FotoPaciente(models.Model):

    CATEGORIA_CHOICES = [
        ('EXTRAORAL_FRONTAL', 'Extraoral Frontal'),
        ('EXTRAORAL_PERFIL', 'Extraoral Perfil'),
        ('INTRAORAL_FRONTAL', 'Intraoral Frontal'),
        ('OCLUSAL_SUP', 'Oclusal Superior'),
        ('OCLUSAL_INF', 'Oclusal Inferior'),
        ('RADIOGRAFIA', 'Radiografía / RX'),
        ('OTRA', 'Otra'),
    ]

    ETAPA_CHOICES = [
        ('INICIAL', 'Inicial (Antes)'),
        ('DIAGNOSTICO', 'Diagnóstico'),
        ('AVANCE', 'Avance de Tratamiento'),
        ('FINAL', 'Final (Después)'),
        ('RETENCION', 'Retención'),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='fotos',
        verbose_name="Paciente"
    )

    imagen = models.ImageField(
        upload_to='fotos_pacientes/%Y/%m/',
        verbose_name="Fotografía"
    )

    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIA_CHOICES,
        default='EXTRAORAL_FRONTAL',
        verbose_name="Categoría / Ángulo"
    )

    etapa = models.CharField(
        max_length=20,
        choices=ETAPA_CHOICES,
        default='INICIAL',
        verbose_name="Etapa del Tratamiento"
    )

    fecha_toma = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de la Fotografía"
    )

    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas / Observaciones"
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Carga"
    )

    class Meta:
        ordering = ['-fecha_toma', '-fecha_registro']
        verbose_name = "Fotografía de Paciente"
        verbose_name_plural = "Fotografías de Pacientes"

    def __str__(self):
        return f"Foto {self.get_categoria_display()} - {self.paciente.nombre_mostrar()} ({self.fecha_toma})"

