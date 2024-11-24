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
            room=Room.objects.get(room_id=room_id)
            room.user_1 =room.user_1  # This will trigger a query to fetch the related User object
            room.user_2 = room.user_2  # This will trigger a query to fetch the related User object
            return room
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
        
    @sync_to_async
    def assign_user_to_room(self, room, user):
        try:
            room.user_2 = user
            room.save()
            return room
        except Exception as e:
            print(f"Error assigning user to room: {e}")
            return None

    async def connect(self):
        print(f"Connecting user: {self.scope['user']}, authenticated: {self.scope['user'].is_authenticated}")
        
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"chat_{self.room_id}"

        room = await self.get_room(self.room_id)
        user = self.scope['user']

        if room is None:
            print(f"Creating new room for user: {user}")
            room = await self.create_room(self.room_id, user)
            if not room:
                print("Room creation failed")
                await self.close()
                return
        else:
            # If room exists but user isn't assigned, assign them as user_2
            if user != room.user_1 and user != room.user_2 and room.user_2 == room.user_1:
                room = await self.assign_user_to_room(room, user)
                if not room:
                    print("Failed to assign user to room")
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
