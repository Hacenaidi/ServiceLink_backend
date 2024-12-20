# views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import AllowAny,IsAuthenticated
from datetime import datetime, timedelta
from .utils import send_code_to_phone,generate_verification_code
from rest_framework_simplejwt.tokens import RefreshToken
from .models import ProfileUser
from .serializers import ProfileUserSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')
    
    if not phone_number or not password:
        return Response({"error": "Phone number and password are required."}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(request, username=phone_number, password=password)
    if user is not None:
        login(request, user)
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Successfully logged in.",
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh)
        }, status=status.HTTP_200_OK)
    
    return Response({"error": "Invalid phone number or password."}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_phone_number(request):
    phone_number = request.data.get('phone_number')

    # Vérification si le numéro est déjà enregistré
    if User.objects.filter(username=phone_number).exists():
        return Response({"error": "Phone number is already registered."}, status=status.HTTP_400_BAD_REQUEST)

    # Générer et envoyer le code de vérification
    code = generate_verification_code()
    send_code_to_phone(phone_number, code)

    # Stocker les informations dans la session
    request.session['verification_code'] = code
    request.session['phone_number_verified'] = False
    request.session['phone_number'] = phone_number
    request.session['code_generated_at'] = str(datetime.now())  # Stockage du timestamp
    print("Session data:", request.session.items())
    request.session.save()
    session_key = request.session.session_key
    print("Session key:", session_key)


    return Response({"message": "Code sent to phone number.", "phone_number": phone_number}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_code(request):
    verification_code = request.data.get('verification_code')
    print(verification_code)
    print("Session data:", request.session.items())
    session_key = request.session.session_key
    print("Session key:", session_key)

    # Vérifier si le code est fourni
    if not verification_code:
        return Response({"error": "Verification code is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Récupérer les informations de la session
    session_code = request.session.get('verification_code')
    print(session_code)
   
    code_generated_at = request.session.get('code_generated_at')

    # Vérifier si le code existe dans la session
    if not session_code:
        return Response({"error": "No verification code sent."}, status=status.HTTP_400_BAD_REQUEST)

    # Vérification de la correspondance des codes
    if session_code != verification_code:
        return Response({"error": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)

    # Vérification de l'expiration du code
    if code_generated_at:
        code_generated_at = datetime.fromisoformat(code_generated_at)
        if datetime.now() > code_generated_at + timedelta(minutes=5):
            return Response({"error": "Verification code has expired."}, status=status.HTTP_400_BAD_REQUEST)

    # Marquer le numéro de téléphone comme vérifié
    request.session['phone_number_verified'] = True

    return Response({"message": "Code verified."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_code(request):
    phone_number = request.data.get('phone_number')
    print(phone_number)

    # Vérifier si un numéro de téléphone est stocké dans la session
    if not phone_number:
        return Response({"error": "No phone number found in session."}, status=status.HTTP_400_BAD_REQUEST)

    # Générer et envoyer un nouveau code de vérification
    code = generate_verification_code()
    send_code_to_phone(phone_number, code)

    # Mettre à jour le code de vérification dans la session
    request.session['verification_code'] = code
    request.session['code_generated_at'] = str(datetime.now())  # Stockage du timestamp

    return Response({"message": "Code resent to phone number."}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    try:
        phone_number = request.session.get('phone_number')
        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')

        # Validation des données
        if not phone_number:
            return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not password or not password_confirm:
            return Response({"error": "Password and password confirmation are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if password != password_confirm:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'phone_number_verified' not in request.session or not request.session['phone_number_verified']:
            return Response({"error": "Phone number not verified."}, status=status.HTTP_400_BAD_REQUEST)

        # Vérification si le numéro est déjà enregistré
        if User.objects.filter(username=phone_number).exists():
            return Response({"error": "Phone number is already registered."}, status=status.HTTP_400_BAD_REQUEST)

        # Création de l'utilisateur
        user = User.objects.create(
            username=phone_number,
            password=make_password(password)  # Hash le mot de passe
        )

        # Création du profil utilisateur
        user_profile = ProfileUser.objects.create(
            user=user,
            phone=phone_number
        )

        # Suppression des données de session liées à l'inscription
        request.session.pop('verification_code', None)
        request.session.pop('phone_number_verified', None)
        request.session.pop('phone_number', None)
        request.session.pop('code_generated_at', None)

        return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    profile = ProfileUser.objects.get(user=user)
    serializer = ProfileUserSerializer(profile)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    profile = ProfileUser.objects.get(user=user)
    serializer = ProfileUserSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)