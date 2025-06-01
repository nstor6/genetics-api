from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from animales.models import Animal
from incidencias.models import Incidencia
from tratamientos.models import Tratamiento
from eventos.models import Evento
from notificaciones.models import Notificacion
from logs.models import Log
from .websocket_utils import (
    send_animal_update, 
    send_notification_to_user,
    send_log_to_admins,
    send_incidencia_alert,
    create_and_send_notification
)
from animales.serializers import AnimalSerializer
from incidencias.serializers import IncidenciaSerializer
from tratamientos.serializers import TratamientoSerializer
from eventos.serializers import EventoSerializer
from notificaciones.serializers import NotificacionSerializer
from logs.serializers import LogSerializer


@receiver(post_save, sender=Animal)
def animal_saved(sender, instance, created, **kwargs):
    """Enviar actualización cuando se crea o modifica un animal"""
    serializer = AnimalSerializer(instance)
    action = 'created' if created else 'updated'
    
    send_animal_update(
        animal_id=instance.id,
        action=action,
        animal_data=serializer.data
    )


@receiver(post_delete, sender=Animal)
def animal_deleted(sender, instance, **kwargs):
    """Enviar notificación cuando se elimina un animal"""
    send_animal_update(
        animal_id=instance.id,
        action='deleted',
        animal_data={'id': instance.id, 'chapeta': instance.chapeta}
    )


@receiver(post_save, sender=Incidencia)
def incidencia_saved(sender, instance, created, **kwargs):
    """Enviar alerta cuando se crea una nueva incidencia"""
    if created:
        # Notificar a administradores sobre nueva incidencia
        from usuarios.models import Usuario
        admins = Usuario.objects.filter(rol='admin', activo=True)
        
        for admin in admins:
            send_incidencia_alert(
                usuario=admin,
                animal=instance.animal,
                incidencia_tipo=instance.tipo
            )


@receiver(post_save, sender=Tratamiento)
def tratamiento_saved(sender, instance, created, **kwargs):
    """Notificar cuando se registra un nuevo tratamiento"""
    if created:
        from usuarios.models import Usuario
        
        # Notificar al administrador del animal
        mensaje = f"Nuevo tratamiento registrado: {instance.medicamento} para {instance.animal.chapeta}"
        
        # Notificar a administradores
        admins = Usuario.objects.filter(rol='admin', activo=True)
        for admin in admins:
            create_and_send_notification(
                usuario=admin,
                mensaje=mensaje,
                tipo='informativa',
                relacionado_con_animal=instance.animal
            )


@receiver(post_save, sender=Evento)
def evento_saved(sender, instance, created, **kwargs):
    """Notificar cuando se crea un nuevo evento"""
    if created:
        from usuarios.models import Usuario
        from datetime import date, timedelta
        
        # Si el evento es para hoy o mañana, enviar recordatorio
        today = date.today()
        tomorrow = today + timedelta(days=1)
        evento_date = instance.fecha_inicio.date()
        
        if evento_date in [today, tomorrow]:
            usuarios = Usuario.objects.filter(activo=True)
            
            for usuario in usuarios:
                mensaje = f"Evento programado: {instance.titulo}"
                if evento_date == today:
                    mensaje += " (HOY)"
                else:
                    mensaje += " (MAÑANA)"
                
                create_and_send_notification(
                    usuario=usuario,
                    mensaje=mensaje,
                    tipo='recordatorio',
                    relacionado_con_evento=instance
                )


@receiver(post_save, sender=Notificacion)
def notificacion_saved(sender, instance, created, **kwargs):
    """Enviar notificación por WebSocket cuando se crea una nueva"""
    if created:
        serializer = NotificacionSerializer(instance)
        send_notification_to_user(instance.usuario.id, serializer.data)


@receiver(post_save, sender=Log)
def log_saved(sender, instance, created, **kwargs):
    """Enviar log a administradores cuando se crea uno nuevo"""
    if created:
        serializer = LogSerializer(instance)
        send_log_to_admins(serializer.data)