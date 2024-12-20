from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import ProviderSerializer
from .models import Provider

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_provider_request(request):
    """
    Endpoint pour créer une demande de fournisseur.
    Accessible uniquement aux utilisateurs authentifiés.
    """
    serializer = ProviderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response({"message": "Request submitted successfully."}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_provider_requests(request):
    """
    Endpoint pour lister les demandes de fournisseur.
    Accessible uniquement à l'administrateur.
    """
    providers = Provider.objects.filter(is_approved=False)
    serializer = ProviderSerializer(providers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def approve_provider(request, provider_id):
    """
    Endpoint pour approuver ou rejeter une demande de fournisseur.
    Accessible uniquement à l'administrateur.
    """
    try:
        provider = Provider.objects.get(id=provider_id)
        action = request.data.get('action')  # 'approve' ou 'reject'

        if action == 'approve':
            provider.is_approved = True
            provider.save()
            return Response({"message": "Provider approved."}, status=status.HTTP_200_OK)
        elif action == 'reject':
            provider.delete()
            return Response({"message": "Provider request rejected."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)
    except Provider.DoesNotExist:
        return Response({"error": "Provider request not found."}, status=status.HTTP_404_NOT_FOUND)
