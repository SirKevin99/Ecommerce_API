# apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.users.models import User


# ==============================================================================
# SERIALIZER DE REGISTRO
# ==============================================================================

class RegisterSerializer(serializers.ModelSerializer):
    """
    Valida y crea un nuevo usuario.
    password2 existe solo para validación — nunca se guarda.
    """
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = [
            "email", "first_name", "last_name",
            "phone", "password", "password2"
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Las contraseñas no coinciden."}
            )
        return attrs

    def create(self, validated_data):
        # Eliminamos password2 antes de crear — no es un campo del modelo
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)  # hashea la contraseña
        user.save()
        return user


# ==============================================================================
# SERIALIZER DE LOGIN
# ==============================================================================

class LoginSerializer(serializers.Serializer):
    """
    Valida credenciales y retorna el usuario autenticado.
    No es un ModelSerializer porque no crea ni actualiza nada.
    """
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email    = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            username=email,   # Django usa username internamente, mapeamos email
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                {"credentials": "Email o contraseña incorrectos."}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"account": "Esta cuenta está desactivada."}
            )

        attrs["user"] = user
        return attrs


# ==============================================================================
# SERIALIZER DE PERFIL (LECTURA)
# ==============================================================================

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer de solo lectura para exponer datos del usuario autenticado.
    Nunca expone password ni campos sensibles.
    """
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model  = User
        fields = [
            "id", "email", "first_name", "last_name",
            "full_name", "phone", "role", "created_at"
        ]
        read_only_fields = fields


# ==============================================================================
# SERIALIZER DE ACTUALIZACIÓN DE PERFIL
# ==============================================================================

class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Permite al usuario editar solo sus datos personales.
    El rol y el email no son modificables desde este endpoint
    para evitar escalación de privilegios.
    """
    class Meta:
        model  = User
        fields = ["first_name", "last_name", "phone"]

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name  = validated_data.get("last_name",  instance.last_name)
        instance.phone      = validated_data.get("phone",      instance.phone)
        instance.save()
        return instance


# ==============================================================================
# SERIALIZER DE CAMBIO DE CONTRASEÑA
# ==============================================================================

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError(
                {"new_password": "Las contraseñas nuevas no coinciden."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user