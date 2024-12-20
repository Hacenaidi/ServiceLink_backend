from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_rooms(request):
    chat_rooms = ChatRoom.objects.filter(participants=request.user)
    serializer = ChatRoomSerializer(chat_rooms, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    serializer = MessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(sender=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, room_id):
    chat_rooms = ChatRoom.objects.filter(participants=request.user)
    if not chat_rooms.filter(id=room_id).exists():
        return Response({"error": "Room not found."}, status=404)
    messages = Message.objects.filter(chat_room_id=room_id).order_by('timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)
