from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from notificaciones.models import Notificacion
from notificaciones.serializers import NotificacionSerializer
from logs.models import Log
from logs.serializers import LogSerializer
from animales.models import Animal
from animales.serializers import AnimalSerializer


def send_notification_to_user(user_id, notification_data):
    """
    Enviar notificación en tiempo real a un usuario específico
    """
    channel_layer = get_channel_layer()
    group_name = f'user_{user_id}'
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'notification_message',
            'data': notification_data
        }
    )


def send_broadcast_notification(notification_data):
    """
    Enviar notificación broadcast a todos los usuarios conectados
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        'general_notifications',
        {
            'type': 'broadcast_message',
            'data': notification_data
        }
    )


def send_log_to_admins(log_data):
    """
    Enviar log en tiempo real a todos los administradores
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        'admin_logs',
        {
            'type': 'new_log',
            'data': log_data
        }
    )


def send_animal_update(animal_id, action, animal_data):
    """
    Enviar actualización de animal a usuarios suscritos
    """
    channel_layer = get_channel_layer()
    
    # Enviar a grupo general
    async_to_sync(channel_layer.group_send)(
        'animal_updates',
        {
            'type': f'animal_{action}',
            'data': {
                'id': animal_id,
                'action': action,
                'animal': animal_data
            }
        }
    )
    
    # Enviar a suscriptores específicos del animal
    async_to_sync(channel_layer.group_send)(
        f'animal_{animal_id}',
        {
            'type': f'animal_{action}',
            'data': {
                'id': animal_id,
                'action': action,
                'animal': animal_data
            }
        }
    )


def create_and_send_notification(usuario, mensaje, tipo='informativa', 
                                relacionado_con_animal=None, 
                                relacionado_con_evento=None):
    """
    Crear notificación en BD y enviarla por WebSocket
    """
    # Crear notificación en BD
    notificacion = Notificacion.objects.create(
        usuario=usuario,
        mensaje=mensaje,
        tipo=tipo,
        relacionado_con_animal=relacionado_con_animal,
        relacionado_con_evento=relacionado_con_evento
    )
    
    # Serializar y enviar por WebSocket
    serializer = NotificacionSerializer(notificacion)
    send_notification_to_user(usuario.id, serializer.data)
    
    return notificacion


def create_and_send_log(usuario, tipo_accion, entidad_afectada, entidad_id, 
                       cambios=None, observaciones=None):
    """
    Crear log en BD y enviarlo por WebSocket a admins
    """
    # Crear log en BD
    log = Log.objects.create(
        usuario=usuario,
        tipo_accion=tipo_accion,
        entidad_afectada=entidad_afectada,
        entidad_id=str(entidad_id),
        cambios=cambios,
        observaciones=observaciones
    )
    
    # Serializar y enviar por WebSocket
    serializer = LogSerializer(log)
    send_log_to_admins(serializer.data)
    
    return log


# Funciones de conveniencia para tipos específicos de notificaciones

def send_incidencia_alert(usuario, animal, incidencia_tipo):
    """Enviar alerta de nueva incidencia"""
    mensaje = f"Nueva incidencia detectada: {incidencia_tipo} en animal {animal.chapeta}"
    create_and_send_notification(
        usuario=usuario,
        mensaje=mensaje,
        tipo='alerta_sanitaria',
        relacionado_con_animal=animal
    )


def send_tratamiento_reminder(usuario, animal, tratamiento):
    """Enviar recordatorio de tratamiento"""
    mensaje = f"Recordatorio: Administrar {tratamiento} a animal {animal.chapeta}"
    create_and_send_notification(
        usuario=usuario,
        mensaje=mensaje,
        tipo='recordatorio',
        relacionado_con_animal=animal
    )


def send_evento_reminder(usuario, evento):
    """Enviar recordatorio de evento"""
    mensaje = f"Recordatorio: {evento.titulo} programado para hoy"
    create_and_send_notification(
        usuario=usuario,
        mensaje=mensaje,
        tipo='recordatorio',
        relacionado_con_evento=evento
    )


def send_system_notification(mensaje, usuarios=None):
    """
    Enviar notificación del sistema a usuarios específicos o todos
    """
    from usuarios.models import Usuario
    
    if usuarios is None:
        usuarios = Usuario.objects.filter(activo=True)
    
    for usuario in usuarios:
        create_and_send_notification(
            usuario=usuario,
            mensaje=mensaje,
            tipo='informativa'
        )