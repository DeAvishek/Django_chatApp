from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from .models import Message, Room

class ChatConsumer(AsyncWebsocketConsumer):

    # Wrapping database calls in async functions using sync_to_async

    @sync_to_async
    def get_room(self, room_id):
        try:
            return Room.objects.get(room_id=room_id)
        except Room.DoesNotExist:
            return None

    @sync_to_async
    def save_message(self, user, room, message):
        # Saving the message to the database
        return Message.objects.create(
            user=user,
            room=room,
            message=message
        )

    @sync_to_async
    def create_room(self, room_id, user):
        # Create a room with user_1 and user_2 as the same user
        try:
            return Room.objects.create(room_id=room_id, user_1=user, user_2=user)
        except Exception as e:
            return None  # Return None in case of any error

    async def connect(self):
        # This method is called when the WebSocket is handshaking as part of the connection process
        self.room_id = self.scope['url_route']['kwargs']['room_id']  # Room id for chat
        self.room_group_name = f"chat_{self.room_id}"  # Group name, based on the room

        # Check if the room exists and if the user is part of the room
        room = await self.get_room(self.room_id)  # Async call to get the room

        if room is None:
            # Room does not exist, create a new room
            user = self.scope['user']
            room = await self.create_room(self.room_id, user)  # Use async call to create room
            if not room:
                await self.close()  # If room creation fails, close the connection
                return
        
        # Check if the user is part of the room (either user_1 or user_2)
        user = self.scope['user']
        if user != room.user_1 and user != room.user_2:
            # If the user is not in the room, close the connection
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
        user = self.scope['user']  # Get the authenticated user

        # Get the room object asynchronously
        room = await self.get_room(self.room_id)
        if room is None:
            return  # If room doesn't exist, ignore the message (or handle this as needed)

        # Save the message to the database asynchronously
        message_obj = await self.save_message(user, room, message)

        # Send the message to the group
        timestamp = message_obj.timestamp.astimezone().isoformat()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',  # This triggers the `chat_message` method
                'message': message,
                'user': user.username,
                'timestamp': timestamp
            }
        )

    async def chat_message(self, event):
        # This method is called when the server receives a message from the group
        message = event['message']
        user = event['user']
        timestamp = event['timestamp']

        # Send the message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user,
            'timestamp': timestamp
        }))
