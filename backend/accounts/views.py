from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import logging
from .serializers import UserRegistrationSerializer, UserSerializer, UserDetailSerializer
from .models import User

logger = logging.getLogger(__name__)


@api_view(['POST', 'OPTIONS'])
@permission_classes([permissions.AllowAny])
def register(request):
    """User registration endpoint."""
    if request.method == 'OPTIONS':
        # Handle CORS preflight
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        logger.info(f"Registration request received. Method: {request.method}, Data: {request.data}")
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            response_data = {
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            response = Response(response_data, status=status.HTTP_201_CREATED)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        logger.warning(f"Serializer validation failed: {serializer.errors}")
        error_response = Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        error_response['Access-Control-Allow-Origin'] = '*'
        return error_response
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        error_response = Response(
            {'error': f'Ошибка регистрации: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_response['Access-Control-Allow-Origin'] = '*'
        return error_response


@api_view(['POST', 'OPTIONS'])
@permission_classes([permissions.AllowAny])
def login(request):
    """User login endpoint."""
    if request.method == 'OPTIONS':
        # Handle CORS preflight
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        logger.info(f"Login request received. Method: {request.method}, Data: {request.data}")
        email = request.data.get('email')
        password = request.data.get('password')

        if email is None or password is None:
            error_response = Response(
                {'error': 'Необходимо указать email и пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )
            error_response['Access-Control-Allow-Origin'] = '*'
            return error_response

        user = authenticate(username=email, password=password)
        if user is None:
            error_response = Response(
                {'error': 'Неверные учетные данные'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            error_response['Access-Control-Allow-Origin'] = '*'
            return error_response

        refresh = RefreshToken.for_user(user)
        response_data = {
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        response = Response(response_data, status=status.HTTP_200_OK)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        error_response = Response(
            {'error': f'Ошибка входа: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_response['Access-Control-Allow-Origin'] = '*'
        return error_response


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile."""
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    """Get current user profile."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def test(request):
    """Test endpoint to verify API is working."""
    return Response({
        'message': 'API is working',
        'method': request.method,
        'data': request.data if request.method == 'POST' else None,
    }, status=status.HTTP_200_OK)

