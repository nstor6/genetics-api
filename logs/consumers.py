import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from usuarios.models import Usuario
from .models import Log
from .serializers import LogSerializer


class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Solo admins pueden conectarse a logs en tiempo real"""
        self.user = await self.get_user_from_token()
        
        if (self.user and 
            not isinstance(self.user, AnonymousUser) and 
            self.user.rol == 'admin'):
            
            self.room_group_name = 'admin_logs'
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Confirmar conexión
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Conectado a logs en tiempo real',
                'user_id': self.user.id
            }))
            
        else:
            await self.close(code=4003)  # Forbidden

    async def disconnect(self, close_code):
        """Desconectar del grupo de logs"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Manejar mensajes del cliente"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_recent_logs':
                limit = data.get('limit', 50)
                logs = await self.get_recent_logs(limit)
                
                await self.send(text_data=json.dumps({
                    'type': 'recent_logs',
                    'data': logs
                }))
                
            elif message_type == 'filter_logs':
                filters = data.get('filters', {})
                logs = await self.get_filtered_logs(filters)
                
                await self.send(text_data=json.dumps({
                    'type': 'filtered_logs',
                    'data': logs
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

    async def new_log(self, event):
        """Enviar nuevo log a todos los admins conectados"""
        await self.send(text_data=json.dumps({
            'type': 'new_log',
            'data': event['data']
        }))

    @database_sync_to_async
    def get_user_from_token(self):
        """Extraer usuario del token JWT"""
        try:
            query_string = self.scope.get('query_string', b'').decode()
            token = None
            
            if 'token=' in query_string:
                token = query_string.split('token=')[1].split('&')[0]
            
            if not token:
                return AnonymousUser()
            
            try:
                decoded_token = jwt.decode(
                    token, 
                    settings.SECRET_KEY, 
                    algorithms=['HS256']
                )
                user_id = decoded_token.get('user_id')
                
                if user_id:
                    return Usuario.objects.get(id=user_id)
                    
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Usuario.DoesNotExist):
                pass
                
            return AnonymousUser()
            
        except Exception as e:
            print(f"Error en autenticación WebSocket: {e}")
            return AnonymousUser()

    @database_sync_to_async
    def get_recent_logs(self, limit):
        """Obtener logs recientes"""
        logs = Log.objects.all().order_by('-fecha_hora')[:limit]
        serializer = LogSerializer(logs, many=True)
        return serializer.data

    @database_sync_to_async
    def get_filtered_logs(self, filters):
        """Obtener logs filtrados"""
        queryset = Log.objects.all()
        
        if filters.get('tipo_accion'):
            queryset = queryset.filter(tipo_accion=filters['tipo_accion'])
        
        if filters.get('entidad_afectada'):
            queryset = queryset.filter(entidad_afectada=filters['entidad_afectada'])
        
        if filters.get('usuario_id'):
            queryset = queryset.filter(usuario_id=filters['usuario_id'])
        
        logs = queryset.order_by('-fecha_hora')[:100]
        serializer = LogSerializer(logs, many=True)
        return serializer.data