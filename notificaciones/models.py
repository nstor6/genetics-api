from django.db import models
from django.conf import settings
from animales.models import Animal
from eventos.models import Evento

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('informativa', 'Informativa'),
        ('alerta_sanitaria', 'Alerta Sanitaria'),
        ('recordatorio', 'Recordatorio'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.TextField()
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    visto = models.BooleanField(default=False)
    relacionado_con_animal = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, blank=True, related_name='notificaciones')
    relacionado_con_evento = models.ForeignKey(Evento, on_delete=models.SET_NULL, null=True, blank=True, related_name='notificaciones_evento')

    def __str__(self):
        return f"{self.tipo} - {self.mensaje[:30]}..."

