from rest_framework import serializers
from .models import Provider

class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = ['id','service','cin', 'location', 'proof_document', 'is_approved']

    def validate(self, data):
        if not data.get("proof_document"):
            raise serializers.ValidationError("Proof document is required.")
        # check if the service exists in the database/ the user passes in an id to the service field
        if not data.get("service"):
            raise serializers.ValidationError("Service is required.")
        

        return data


