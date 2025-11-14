from adrf.views import APIView
from django.conf import settings
from django.contrib.auth import aauthenticate, get_user_model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from users.permissions import IsAdmin, IsSelfOrAdmin
from users.serializers import UserSerializer

from .serializers import LoginRequestSerializer, LoginResponseSerializer

User = get_user_model()


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User Login and JWT Cookie Generation",
        description="Authenticates the user and sets Access and Refresh JWT tokens in **HttpOnly cookies**.",
        # 1. Request Body Schema
        request=LoginRequestSerializer,
        # 2. Response Schema (Success and Failure)
        responses={
            200: LoginResponseSerializer,
            400: OpenApiTypes.OBJECT, # Simple error object
        },
        # 3. Examples for clarity
        examples=[
            OpenApiExample(
                'Successful Login',
                value={'message': 'Login successful.', 'username': 'testuser'},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Invalid Credentials',
                value={'error': 'Invalid credentials.'},
                response_only=True,
                status_codes=['400']
            ),
        ]
    )
    async def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        input_serializer = LoginRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        user = await aauthenticate(request, username=username, password=password)

        if user is not None:
            # Generate both access and refresh tokens
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            # Prepare the response
            response = Response({
                'message': 'Login successful.',
                'username': user.username,
            }, status=status.HTTP_200_OK)

            # Set cookies with HttpOnly and secure flags
            response.set_cookie(
                key=str(settings.SIMPLE_JWT['AUTH_COOKIE']),
                value=str(access),
                expires=str(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']),
                secure=bool(settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']),
                httponly=bool(settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY']),
                samesite=str(settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'])
            )
            response.set_cookie(
                key=str(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH']),
                value=str(refresh),
                expires=str(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']),
                secure=bool(settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']),
                httponly=bool(settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY']),
                samesite=str(settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'])
            )

            return response
        else:
            return Response({
                'error': 'Invalid credentials.'
            }, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])

        if not refresh_token:
            raise AuthenticationFailed('Refresh token is missing.')

        try:
            # Use Simple JWT's built-in serializer to validate the refresh token
            serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
            serializer.is_valid(raise_exception=True)
            # validated_data can be None in some type-checking scenarios; guard and use .get
            validated = getattr(serializer, 'validated_data', None) or {}
            new_access_token = validated.get('access')
            if not new_access_token:
                # If access token is missing after validation, treat as authentication failure
                raise AuthenticationFailed('Failed to refresh access token.')

            # Prepare the response and set the new access token cookie
            response = Response({'message': 'Access token refreshed.'}, status=status.HTTP_200_OK)
            response.set_cookie(
                key=str(settings.SIMPLE_JWT['AUTH_COOKIE']),
                value=str(new_access_token),
                expires=str(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']),
                secure=bool(settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']),
                httponly=bool(settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY']),
                samesite=str(settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'])
            )
            return response

        except AuthenticationFailed:
            # Re-raise authentication failures unchanged
            raise
        except Exception:
            raise AuthenticationFailed('Refresh token is invalid or expired.')


class UserCreateView(CreateModelMixin, GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Handles the POST request to create a new user
        return self.create(request, *args, **kwargs)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        # Use different permissions based on the action
        if self.action == 'list':
            # Only admins can view the list of all users
            permission_classes = [IsAdmin]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For specific user objects, allow admins or the user themselves
            permission_classes = [IsSelfOrAdmin]
        else:
            # For other actions (like 'create'), allow any authenticated user
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
