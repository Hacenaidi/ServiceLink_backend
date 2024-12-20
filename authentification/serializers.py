from rest_framework import serializers
from .models import ProfileUser


class ProfileUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileUser
        fields = ['id','img','age', 'nom', 'prenom', 'phone', 'location', 'bio']

    def validate(self, data):
        if not data.get("phone"):
            raise serializers.ValidationError("Phone number is required.")
        return data