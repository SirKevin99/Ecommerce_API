# apps/users/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema

from apps.users.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
)
from apps.users.services import AuthService


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserProfileSerializer},
        summary="Registrar nuevo usuario",
        description="Endpoint público — no requiere autenticación. Crea el usuario y retorna tokens listos para usar."
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_data = AuthService.build_auth_response(user)
        return Response(response_data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: UserProfileSerializer},
        summary="Iniciar sesión",
        description="Valida credenciales y retorna tokens JWT de acceso y refresco."
    )
    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        response_data = AuthService.build_auth_response(user)
        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: None},
        summary="Cerrar sesión",
        description="Invalida el refresh token. Enviá el refresh token en el body."
    )
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


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileSerializer},
        summary="Ver perfil",
        description="Retorna los datos del usuario autenticado."
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UpdateProfileSerializer,
        responses={200: UpdateProfileSerializer},
        summary="Actualizar perfil",
        description="Actualiza nombre, apellido y teléfono del usuario."
    )
    def patch(self, request):
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: None},
        summary="Cambiar contraseña",
        description="Requiere la contraseña actual y la nueva dos veces."
    )
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