from django.db import models
from django.conf import settings

class Log(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    tipo_accion = models.CharField(max_length=50)
    entidad_afectada = models.CharField(max_length=100)
    entidad_id = models.CharField(max_length=100)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    cambios = models.JSONField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo_accion} en {self.entidad_afectada} ({self.entidad_id})"

