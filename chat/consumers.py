import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

# Setup logging
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        token = self.get_token_from_headers(self.scope['headers'])
        self.user = await self.get_user_from_token(token)

        # Use the token to authenticate the user
        self.user = await self.authenticate_user(token)

        if not self.user:
            await self.close()
            return
        
        
        # Check if the room exists or create it if the user is verified
        if not await self.room_exists(self.room_name):
            if not await self.is_verified_provider(self.user):
                logger.error("User is not a verified provider. Closing connection.")
                await self.close()
                return
            else:
                self.room_user = self.scope['url_route']['kwargs']['room_user']
                if self.room_user != self.user.username:
                    # add the provided user to the room
                    from django.contrib.auth.models import User
                    # get the user by id and add to the room
                    try:
                        user = await self.get_user_by_id(self.room_user)
                        await self.create_room(self.room_name)
                        await self.add_user_to_room(self.room_name, user)
                        await self.add_user_to_room(self.room_name, self.user)
                    except User.DoesNotExist:
                        logger.error(f"User with id {self.room_user} does not exist.")
                        await self.close()
                        return                    


        if not await self.check_user_in_room(self.room_name, self.user):
            # close the connection if the user is not in the room
            logger.error("User is not in the room. Closing connection.")
            await self.close()
            return
            

        # Add the user to the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"User {self.user} connected to room {self.room_name}.")

    async def disconnect(self, close_code):
        # Remove the user from the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"User {self.user} disconnected from room {self.room_name}.")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            recipient_username = text_data_json.get('recipient', '')

            if not message:
                logger.warning("Empty message received. Ignoring.")
                return

            # Notify the recipient user if they exist
            recipient = await self.get_user_by_username(recipient_username)
            if recipient:
                await self.notify_user(recipient)
            await self.save_message(self.room_name, self.user, message)
            # Broadcast the message to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': self.user.username
                }
            )
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message.")
        except Exception as e:
            logger.exception(f"Unexpected error in receive: {e}")

    async def chat_message(self, event):
        message = event['message']
        sender = event.get('sender', 'Unknown')

        # Send the message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))

    # Utility methods
    @sync_to_async
    def is_verified_provider(self, user):
        """Check if the user is a verified provider."""
        from provider.models import Provider  # Deferred import
        try:
            provider_profile = Provider.objects.get(user=user)
            return provider_profile.is_approved
        except Provider.DoesNotExist:
            logger.error(f"No provider profile found for user {user}.")
            return False

    @sync_to_async
    def room_exists(self, room_name):
        """Check if the chat room exists."""
        from chat.models import ChatRoom  # Deferred import
        return ChatRoom.objects.filter(name=room_name).exists()

    @sync_to_async
    def create_room(self, room_name):
        """Create a new chat room."""
        from chat.models import ChatRoom  # Deferred import
        logger.info(f"Creating new chat room: {room_name}.")
        ChatRoom.objects.create(name=room_name)

    @sync_to_async
    def get_user_by_username(self, username):
        """Retrieve a user by their username."""
        from django.contrib.auth.models import User  # Deferred import
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning(f"User with username {username} does not exist.")
            return None

    @sync_to_async
    def notify_user(self, user):
        """Implement notification logic for the user."""
        # Example placeholder logic for notifying a user
        logger.info(f"Notifying user {user.username}.")
        pass

    @sync_to_async
    def authenticate_user(self, token):
        """Authenticate user using the JWT token."""
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth.models import User
        try:
            # Decode and verify the token
            print(token)
            access_token = AccessToken(token)
            print(access_token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
        
        
    @sync_to_async
    def get_user_from_token(self, token):
        """Retrieve a user from the JWT token."""
        
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth.models import User
        from django.contrib.auth.models import AnonymousUser
        
        try:
            access_token = AccessToken(token)
            print(access_token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except Exception as e:
            logger.error(f"Failed to authenticate user from token: {e}")
            return AnonymousUser()
        
        
        
    @sync_to_async
    def add_user_to_room(self, room_name, user):
        """Add a user to the chat room participants."""
        from chat.models import ChatRoom  # Deferred import
        room = ChatRoom.objects.get(name=room_name)
        room.participants.add(user)
        room.save()
        logger.info(f"Added user {user} to room {room_name}.")

        
    @sync_to_async
    def check_user_in_room(self, room_name, user):
        """Check if the user is in the chat room participants."""
        from chat.models import ChatRoom  # Deferred import
        room = ChatRoom.objects.get(name=room_name)
        return room.participants.filter(id=user.id).exists()
    
        
    @sync_to_async
    def save_message(self, room_name, user, message):
        """Save a message to the database."""
        from chat.models import ChatRoom, Message  # Deferred import
        room = ChatRoom.objects.get(name=room_name)
        Message.objects.create(chat_room=room, sender=user, content=message)
        logger.info(f"Message from {user.username} saved to room {room_name}.")    
        
    @sync_to_async
    def get_user_by_id(self, user_id):
        """Retrieve a user by their ID."""
        from django.contrib.auth.models import User  # Deferred import
        return User.objects.get(id=user_id)
    
    def get_token_from_headers(self, headers):
        """Extract JWT token from headers."""
        for key, value in headers:
            if key == b'authorization':           
                return value.decode('utf-8').split()[1]
            
        return None