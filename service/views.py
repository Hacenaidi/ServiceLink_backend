from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from service.serializers import OrderSerializer, OfferSerializer, OrderMediaSerializer, ServiceSerializer
from .models import Service, Order, offer, OrderMedia
from provider.models import Provider
from django.db.models import Q,Subquery, OuterRef
from django.contrib.auth.models import User

# Créer une commande
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    try:
        client = request.user  # Le client est l'utilisateur connecté
        service_id = request.data.get('service_id')
        title = request.data.get('title')
        description = request.data.get('description')
        location = request.data.get('location')
        proposed_price_range_min = request.data.get('proposed_price_range_min')
        proposed_price_range_max = request.data.get('proposed_price_range_max')
        provider = request.data.get('Confirmed_provider')

        # Vérifier si le service existe
        service = Service.objects.filter(id=service_id).first()
        if not service:
            return Response({"error": "Service not found."}, status=status.HTTP_404_NOT_FOUND)
        # Créer un dictionnaire de données pour la validation
        order_data = {
            "STATES":"pending",
            'client': client.id,
            'service': service.id,
            'title': title,
            'description': description,
            'location': location,
            'Confirmed_provider': provider if provider else None,
            'proposed_price_range_min': proposed_price_range_min,
            'proposed_price_range_max': proposed_price_range_max,
            'final_price': proposed_price_range_min,
            'accepted_offer': None,
        }

        # Sérialiser et valider les données
        order_serializer = OrderSerializer(data=order_data)
        if order_serializer.is_valid():
            # Si les données sont valides, créer la commande
            order = order_serializer.save()

            # Gérer les fichiers multimédias
            media_files = request.FILES.getlist('media')
            if media_files:
                for media_file in media_files:
                    OrderMedia.objects.create(order=order, file=media_file)

            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Si les données ne sont pas valides, renvoyer les erreurs de validation
            return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Lister toutes les offres pour une commande spécifique
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_order_offers(request, order_id):
    try:
        # Récupérer la commande par son ID
        order = Order.objects.filter(id=order_id).first()
        if not order:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        # Récupérer les offres pour la commande
        offers = offer.objects.filter(order=order)
        offer_serializer = OfferSerializer(offers, many=True)

        return Response({"offers": offer_serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Accepter une offre
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_offer(request):
    try:
        order_id = request.data.get('order_id')
        offer_id = request.data.get('offer_id')
        provider = request.user.provider  # L'utilisateur connecté est le fournisseur

        if not provider:
            return Response({"error": "Provider not found."}, status=status.HTTP_404_NOT_FOUND)

        # Récupérer la commande et l'offre
        order = Order.objects.filter(id=order_id).first()
        selected_offer = offer.objects.filter(id=offer_id).first()  # Renommer la variable pour éviter le conflit

        if not order:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if not selected_offer:
            return Response({"error": "Offer not found."}, status=status.HTTP_404_NOT_FOUND)

        # Accepter l'offre et mettre à jour l'état de la commande
        order.accepted_offer = selected_offer
        order.STATES = 'accepted'
        order.final_price = selected_offer.proposed_price
        order.Confirmed_provider = provider
        order.save()

        # Sérialiser la commande mise à jour
        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_provider_available_orders(request):
    try:
        # Récupérer le fournisseur à partir de l'utilisateur authentifié
        user = request.user
        provider = Provider.objects.get(user=user)

        # Récupérer l'ID du service du fournisseur
        service_id = provider.service.id

        # Récupérer les commandes en attente pour le service du fournisseur où Confirmed_provider est soit None, soit le fournisseur authentifié
        # et filtrer les commandes qui n'ont pas d'offre avec ce fournisseur
        orders = Order.objects.filter(
            Q(service=service_id) & (Q(Confirmed_provider=None) | Q(Confirmed_provider=provider))
        ).exclude(
            id__in=Subquery(
                offer.objects.filter(provider=provider, order=OuterRef('id')).values('Order')
            )
        ).order_by('-created_at')

        # Sérialiser les données des commandes
        order_serializer = OrderSerializer(orders, many=True)

        return Response({"orders": order_serializer.data}, status=status.HTTP_200_OK)

    except Provider.DoesNotExist:
        return Response({"error": "Provider not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# Créer une offre pour une commande
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_offer(request):
    try:
        provider = request.user.provider  # L'utilisateur connecté est le fournisseur
        order_id = request.data.get('order_id')
        proposed_price = request.data.get('proposed_price')
        description = request.data.get('description')

        # Vérifier si la commande existe
        order = Order.objects.filter(id=order_id).first()
        if not order:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        # Préparer les données pour l'offre
        offer_data = {
            'provider': provider.id,  # Assurez-vous que `provider` est l'ID, pas l'objet.
            'Order': order.id,        # De même pour `order`.
            'proposed_price': proposed_price,
            'description': description
        }
        
        # Sérialiser et valider les données de l'offre
        offer_serializer = OfferSerializer(data=offer_data)
        if offer_serializer.is_valid():
            offer = offer_serializer.save()
            return Response(offer_serializer.data, status=status.HTTP_201_CREATED)
        else:
            # En cas d'erreurs de validation, renvoyer les erreurs
            return Response(offer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Lister les services
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_service(request):
    try:
        services = Service.objects.all()
        service_serializer = ServiceSerializer(services, many=True)
        return Response(service_serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# list order by client
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_client_orders(request):
    try:
        client = request.user
        # Récupérer les commandes du client en ordre décroissant de la date de création
        orders = Order.objects.filter(client=client).order_by('-created_at')
        order_serializer = OrderSerializer(orders, many=True)
        return Response(order_serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# path('order/<int:order_id>/', views.get_order, name='order'),
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order(request, order_id):

    #test if is a provider
    try:
        user = request.user
        provider = Provider.objects.get(user=user)
        if provider:
            order = Order.objects.filter(id=order_id).first()
            if not order:
                return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)
    except Provider.DoesNotExist:
        return Response({"error": "Provider not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Reject an oder de creete un offer et modifiy accpted to flase

@api_view(['POST'])
@permission_classes([IsAuthenticated])

def reject_offer(request):
    try:
        provider = request.user.provider  # L'utilisateur connecté est le fournisseur
        if not provider:
            return Response({"error": "Provider not found."}, status=status.HTTP_404_NOT_FOUND)
        
        order_id = request.data.get('order_id')
        # Vérifier si la commande existe
        order = Order.objects.filter(id=order_id).first()
        if not order:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        # Préparer les données pour l'offre
        offer_data = {
            'provider': provider.id,  # Assurez-vous que `provider` est l'ID, pas l'objet.
            'Order': order.id,        # De même pour `order`.
            'proposed_price': None,
            'description': None,
            'accepted': False
        }

        # Sérialiser et valider les données de l'offre
        offer_serializer = OfferSerializer(data=offer_data)
        if offer_serializer.is_valid():
            offer = offer_serializer.save()
            return Response(offer_serializer.data, status=status.HTTP_201_CREATED)
        else:
            # En cas d'erreurs de validation, renvoyer les erreurs
            return Response(offer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


# Complete an order
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_order(request):
    try:
        order_id = request.data.get('order_id')
        order = Order.objects.filter(id=order_id).first()
        if not order:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        order.STATES = 'completed'
        order.save()
        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

#cancel an order
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_order(request):
    try:
        order_id = request.data.get('order_id')
        order = Order.objects.filter(id=order_id).first()
        if not order:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        order.STATES = 'rejected'
        order.save()
        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    