from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

Usuario = get_user_model()

class Animal(models.Model):
    SEXO_CHOICES = [
        ('macho', 'Macho'),
        ('hembra', 'Hembra'),
    ]

    ESTADO_REPRODUCTIVO_CHOICES = [
        ('gestante', 'Gestante'),
        ('lactante', 'Lactante'),
        ('vacío', 'Vacío'),
        ('castrado', 'Castrado'),
    ]

    ESTADO_PRODUCTIVO_CHOICES = [
        ('activo', 'Activo'),
        ('retirado', 'Retirado'),
        ('engorde', 'Engorde'),
    ]

    chapeta = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    sexo = models.CharField(max_length=10, choices=SEXO_CHOICES)
    fecha_nacimiento = models.DateField()
    raza = models.CharField(max_length=100)
    estado_reproductivo = models.CharField(max_length=20, choices=ESTADO_REPRODUCTIVO_CHOICES)
    estado_productivo = models.CharField(max_length=20, choices=ESTADO_PRODUCTIVO_CHOICES)
    salud = models.JSONField(default=list, blank=True)
    produccion = models.JSONField(default=list, blank=True)
    peso_actual = models.FloatField(null=True, blank=True)
    ubicacion_actual = models.CharField(max_length=255, blank=True, null=True)
    historial_movimientos = models.JSONField(default=list, blank=True)
    descendencia = models.ManyToManyField('self', symmetrical=False, blank=True)
    fecha_alta_sistema = models.DateTimeField(default=timezone.now)
    fecha_baja_sistema = models.DateTimeField(blank=True, null=True)
    foto_perfil_url = models.URLField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(Usuario, related_name='animales_creados', on_delete=models.SET_NULL, null=True)
    modificado_por = models.ForeignKey(Usuario, related_name='animales_modificados', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.chapeta} - {self.nombre or 'Sin nombre'}"
