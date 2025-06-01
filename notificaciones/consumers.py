import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from usuarios.models import Usuario
from .models import Notificacion
from .serializers import NotificacionSerializer


class NotificacionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Conectar usuario autenticado"""
        self.user = await self.get_user_from_token()
        
        if self.user and not isinstance(self.user, AnonymousUser):
            self.room_group_name = f'user_{self.user.id}'
            
            # Unirse al grupo personal del usuario
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Unirse al grupo general de notificaciones
            await self.channel_layer.group_add(
                'general_notifications',
                self.channel_name
            )
            
            await self.accept()
            
            # Enviar notificaciones pendientes
            await self.send_pending_notifications()
            
            # Confirmar conexión
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Conectado a notificaciones en tiempo real',
                'user_id': self.user.id
            }))
        else:
            await self.close(code=4001)  # Unauthorized

    async def disconnect(self, close_code):
        """Desconectar usuario"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.channel_layer.group_discard(
                'general_notifications',
                self.channel_name
            )

    async def receive(self, text_data):
        """Recibir mensajes del cliente"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_as_read':
                notification_id = data.get('notification_id')
                success = await self.mark_notification_as_read(notification_id)
                
                await self.send(text_data=json.dumps({
                    'type': 'notification_read_response',
                    'notification_id': notification_id,
                    'success': success
                }))
                
            elif message_type == 'get_unread_count':
                count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': count
                }))
                
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato JSON inválido'
            }))

    async def notification_message(self, event):
        """Enviar notificación al cliente"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data']
        }))

    async def broadcast_message(self, event):
        """Mensaje broadcast a todos los usuarios"""
        await self.send(text_data=json.dumps({
            'type': 'broadcast',
            'data': event['data']
        }))

    @database_sync_to_async
    def get_user_from_token(self):
        """Extraer usuario del token JWT"""
        try:
            # Obtener token de query parameters
            query_string = self.scope.get('query_string', b'').decode()
            token = None
            
            if 'token=' in query_string:
                token = query_string.split('token=')[1].split('&')[0]
            
            if not token:
                return AnonymousUser()
            
            # Decodificar token JWT
            try:
                decoded_token = jwt.decode(
                    token, 
                    settings.SECRET_KEY, 
                    algorithms=['HS256']
                )
                user_id = decoded_token.get('user_id')
                
                if user_id:
                    return Usuario.objects.get(id=user_id)
                    
            except jwt.ExpiredSignatureError:
                print("Token expirado")
            except jwt.InvalidTokenError:
                print("Token inválido")
            except Usuario.DoesNotExist:
                print("Usuario no encontrado")
                
            return AnonymousUser()
            
        except Exception as e:
            print(f"Error en autenticación WebSocket: {e}")
            return AnonymousUser()

    @database_sync_to_async
    def send_pending_notifications(self):
        """Enviar notificaciones no leídas"""
        try:
            notifications = Notificacion.objects.filter(
                usuario=self.user,
                visto=False
            ).order_by('-fecha_creacion')[:10]
            
            for notification in notifications:
                serializer = NotificacionSerializer(notification)
                # Usar async_to_sync para el envío
                from asgiref.sync import async_to_sync
                async_to_sync(self.send)(text_data=json.dumps({
                    'type': 'pending_notification',
                    'data': serializer.data
                }))
                
        except Exception as e:
            print(f"Error enviando notificaciones pendientes: {e}")

    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """Marcar notificación como leída"""
        try:
            notification = Notificacion.objects.get(
                id=notification_id,
                usuario=self.user
            )
            notification.visto = True
            notification.save()
            return True
        except Notificacion.DoesNotExist:
            return False

    @database_sync_to_async
    def get_unread_count(self):
        """Obtener contador de notificaciones no leídas"""
        return Notificacion.objects.filter(
            usuario=self.user,
            visto=False
        ).count()