# chat/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from django.contrib.auth.models import User
from .models import Message ,Room
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # This method is called when the WebSocket is handshaking as part of the connection process
        self.room_id = 112024  # Room name for chat
        self.room_group_name = f"chat_{self.room_id}"  # Group name, based on the room

        # Check if the room exists and if the user is part of the room
        try:
            room=Room.objects.get(room_id=self.room_id)
            user=self.scope['user']
            if user!=room.user_1 and user !=room.user_2:
                # If the user is not in the room, close the connection
                await self.close()
                return
        except Room.DoesNotExist:
            await self.close()
            return 
        # Join the WebSocket group  
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # This method is called when the WebSocket closes
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # This method is called when the server receives a message from WebSocket
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user=self.scope['user'] #get the authenticate user
        
        
        # Get the room object
        try:
            room=Room.objects.get(room_id=self.room_id)
        except Room.DoesNotExist:
            return
        
        # Save the message to the database
        message_obj=Message.objects.create(
            user=user,
            room=room,
            message=message
        )

        # Send the message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',  # This triggers the `chat_message` method
                'message': message,
                'user':user.username,
                'timestamp':message_obj.timestamp.isoformat()
            }
        )

    async def chat_message(self, event):
        # This method is called when the server receives a message from the group
        message = event['message']
        user=event['user']
        timestamp=event['tmestamp']

        # Send the message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user':user,
            'timestamp':timestamp
        }))
