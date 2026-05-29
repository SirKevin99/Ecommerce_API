# apps/users/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.users.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
)
from apps.users.services import AuthService


# ==============================================================================
# REGISTRO
# ==============================================================================

class RegisterView(APIView):
    """
    Endpoint público — no requiere autenticación.
    Crea el usuario y retorna tokens listos para usar.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_data = AuthService.build_auth_response(user)
        return Response(response_data, status=status.HTTP_201_CREATED)


# ==============================================================================
# LOGIN
# ==============================================================================

class LoginView(APIView):
    """
    Valida credenciales y retorna tokens JWT.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        response_data = AuthService.build_auth_response(user)
        return Response(response_data, status=status.HTTP_200_OK)


# ==============================================================================
# LOGOUT
# ==============================================================================

class LogoutView(APIView):
    """
    Invalida el refresh token en la blacklist.
    El access token expira solo según SIMPLE_JWT settings.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "El refresh token es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            AuthService.blacklist_token(refresh_token)
            return Response(
                {"detail": "Sesión cerrada correctamente."},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"detail": "Token inválido o expirado."},
                status=status.HTTP_400_BAD_REQUEST
            )


# ==============================================================================
# PERFIL
# ==============================================================================

class ProfileView(APIView):
    """
    GET  → retorna datos del usuario autenticado
    PATCH → actualiza datos personales (no rol, no email)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# ==============================================================================
# CAMBIO DE CONTRASEÑA
# ==============================================================================

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK
        )