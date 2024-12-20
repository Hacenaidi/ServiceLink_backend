import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from users.models import Provider
from chat.models import ChatRoom, Message

# Setup logging
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        # Log the connection attempt
        logger.debug(f"User {self.user} attempting to connect to room {self.room_name}.")

        if not self.user.is_authenticated:
            logger.error("User is not authenticated. Closing connection.")
            await self.close()
            return

        # Check if the room exists or create it if the user is verified
        if not await self.room_exists(self.room_name):
            if not await self.is_verified_provider(self.user):
                logger.error("User is not a verified provider. Closing connection.")
                await self.close()
                return
            else:
                await self.create_room(self.room_name)

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
        try:
            provider_profile = Provider.objects.get(user=user)
            return provider_profile.is_verified
        except Provider.DoesNotExist:
            logger.error(f"No provider profile found for user {user}.")
            return False

    @sync_to_async
    def room_exists(self, room_name):
        """Check if the chat room exists."""
        return ChatRoom.objects.filter(name=room_name).exists()

    @sync_to_async
    def create_room(self, room_name):
        """Create a new chat room."""
        logger.info(f"Creating new chat room: {room_name}.")
        ChatRoom.objects.create(name=room_name)

    @sync_to_async
    def get_user_by_username(self, username):
        """Retrieve a user by their username."""
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
