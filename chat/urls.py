from django.urls import path
from . import views

urlpatterns = [
    path('chat-rooms/', views.get_chat_rooms, name='get_chat_rooms'),
    path('send-message/', views.send_message, name='send_message'),
    path('messages/<int:room_id>/', views.get_messages, name='get_messages'),
]