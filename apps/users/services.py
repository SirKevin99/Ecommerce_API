# apps/users/services.py
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import User


# ==============================================================================
# POR QUÉ UN SERVICE?
# La vista no debe saber cómo se generan los tokens ni cómo se construye
# la respuesta de autenticación. Eso es responsabilidad del service.
# La vista solo orquesta: recibe request → llama service → retorna response.
# ==============================================================================

class AuthService:

    @staticmethod
    def get_tokens_for_user(user: User) -> dict:
        """
        Genera el par de tokens JWT para un usuario.
        Retorna access y refresh token como strings.
        """
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access":  str(refresh.access_token),
        }

    @staticmethod
    def get_user_data(user: User) -> dict:
        """
        Construye el payload de respuesta del usuario autenticado.
        Centraliza qué datos se exponen en login y register.
        """
        from apps.users.serializers import UserProfileSerializer
        return UserProfileSerializer(user).data

    @staticmethod
    def build_auth_response(user: User) -> dict:
        """
        Combina tokens + datos del usuario en una sola respuesta.
        Usado tanto en register como en login para consistencia.
        """
        tokens    = AuthService.get_tokens_for_user(user)
        user_data = AuthService.get_user_data(user)
        return {
            "user":   user_data,
            "tokens": tokens,
        }

    @staticmethod
    def blacklist_token(refresh_token: str) -> None:
        """
        Invalida el refresh token en el logout.
        Requiere que token_blacklist esté en INSTALLED_APPS.
        """
        token = RefreshToken(refresh_token)
        token.blacklist()