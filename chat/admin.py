from django.contrib import admin

# Register your models here.


from .models import Message, ChatRoom

admin.site.register(Message)
admin.site.register(ChatRoom)