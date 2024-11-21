from django.forms import ValidationError
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

@api_view(['POST'])
def register(request):
    if request.method == 'POST':
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response({
                    "message": "Registration successful",
                    "user_id": user.id  # Use the saved user's ID
                }, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                # Handle Django validation errors
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                # Log exception if needed
                return Response({
                    "error": "An unexpected error occurred.",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Return serializer validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login(request):
    """Login a user and return JWT tokens."""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        # Get authenticated user and tokens
        tokens = serializer.get_tokens()
        return Response({
            'message': 'Login successful',
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
        }, status=status.HTTP_200_OK)

    # Return validation errors if any
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": "This is a protected view"})