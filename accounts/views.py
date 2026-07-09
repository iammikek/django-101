"""Account serializers and auth views."""

from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from catalog.exceptions import UserEmailExistsError
from catalog.throttles import AuthRateThrottle

User = get_user_model()


class UserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=5, max_length=255)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)


class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email"]


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.EmailField(help_text="Email address (FastAPI parity field name)")
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    token_type = serializers.CharField()


@extend_schema(
    request=UserCreateSerializer,
    responses={201: UserResponseSerializer, 409: OpenApiResponse(description="Email already exists")},
)
class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        if User.objects.filter(email=email).exists():
            raise UserEmailExistsError(email)
        user = User.objects.create_user(
            email=email,
            password=serializer.validated_data["password"],
        )
        return Response(UserResponseSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=LoginRequestSerializer,
    responses={
        200: LoginResponseSerializer,
        401: OpenApiResponse(description="Incorrect email or password"),
    },
)
class LoginView(APIView):
    """Exchange email + password for a JWT (username field holds email, like FastAPI)."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        email = request.data.get("username") or request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            raise serializers.ValidationError({"detail": "Email and password are required"})
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {"detail": "Incorrect email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        access_token = str(AccessToken.for_user(user))
        return Response({"access_token": access_token, "token_type": "bearer"})


@extend_schema(responses={200: UserResponseSerializer})
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserResponseSerializer(request.user).data)
