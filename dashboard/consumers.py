import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ChatRoom, ChatMessage, ChatParticipant

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Update user online status
        if not isinstance(self.user, AnonymousUser):
            await self.update_user_online_status(True)
            
            # Send join notification
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'username': self.user.get_full_name() or self.user.email,
                    'is_online': True,
                    'message': 'joined the chat'
                }
            )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Update user offline status
        if not isinstance(self.user, AnonymousUser):
            await self.update_user_online_status(False)
            
            # Send leave notification
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'username': self.user.get_full_name() or self.user.email,
                    'is_online': False,
                    'message': 'left the chat'
                }
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            message = text_data_json['message']
            
            # Save message to database
            saved_message = await self.save_message(message)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'message_id': saved_message.id,
                    'sender_id': self.user.id,
                    'sender_name': self.user.get_full_name() or self.user.email,
                    'timestamp': saved_message.created_at.isoformat(),
                }
            )
        
        elif message_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'username': self.user.get_full_name() or self.user.email,
                    'is_typing': text_data_json['is_typing']
                }
            )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
        }))

    async def user_status(self, event):
        # Send user status update
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_online': event['is_online'],
            'message': event['message'],
        }))

    async def typing_indicator(self, event):
        # Send typing indicator
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing'],
        }))

    @database_sync_to_async
    def save_message(self, message_content):
        """Save message to database"""
        room = ChatRoom.objects.get(room_id=self.room_id)
        message = ChatMessage.objects.create(
            room=room,
            sender=self.user,
            content=message_content,
            message_type='text'
        )
        return message

    @database_sync_to_async
    def update_user_online_status(self, is_online):
        """Update user online status"""
        room = ChatRoom.objects.get(room_id=self.room_id)
        participant, created = ChatParticipant.objects.get_or_create(
            user=self.user,
            room=room
        )
        participant.is_online = is_online
        participant.save()