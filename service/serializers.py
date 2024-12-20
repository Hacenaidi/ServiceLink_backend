from rest_framework import serializers
from .models import Order, offer, Service, OrderMedia

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class OfferSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.user.username', read_only=True)

    class Meta:
        model = offer
        fields = '__all__'


class OrderMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderMedia
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.username', read_only=True)
    offers = OfferSerializer(many=True, read_only=True)
    accepted_offer = OfferSerializer(read_only=True)
    media = OrderMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

    def validate(self, data):
        if data['proposed_price_range_min'] > data['proposed_price_range_max']:
            raise serializers.ValidationError("The minimum price cannot be greater than the maximum price.")
        return data

    def validate_location(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Location name is too short. Please provide a detailed location.")
        return value

    def validate_description(self, value):
        if len(value) < 20:
            raise serializers.ValidationError("Description is too short. It should have at least 20 characters.")
        return value