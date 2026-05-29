# apps/users/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


# ==============================================================================
# MANAGER PERSONALIZADO
# ==============================================================================

class UserManager(BaseUserManager):
    """
    Manager personalizado para el modelo User.
    Necesario porque usamos email como campo de autenticación
    en lugar del username por defecto de Django.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hashea la contraseña automáticamente
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


# ==============================================================================
# MODELO DE USUARIO
# ==============================================================================

class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado.

    Por qué extender AbstractBaseUser y no AbstractUser:
    - AbstractUser asume username como campo principal
    - AbstractBaseUser nos da control total sobre los campos de autenticación
    - Podemos definir email como campo de login desde el inicio
    """

    class Role(models.TextChoices):
        ADMIN     = "admin",    "Administrador"
        CUSTOMER  = "customer", "Cliente"
        STAFF     = "staff",    "Staff"

    # ------------------------------------------------------------------
    # Campos de identidad
    # ------------------------------------------------------------------
    email       = models.EmailField(unique=True)
    first_name  = models.CharField(max_length=100)
    last_name   = models.CharField(max_length=100)
    phone       = models.CharField(max_length=20, blank=True)

    # ------------------------------------------------------------------
    # Rol y permisos
    # ------------------------------------------------------------------
    role        = models.CharField(
                    max_length=20,
                    choices=Role.choices,
                    default=Role.CUSTOMER
                  )

    # ------------------------------------------------------------------
    # Estado de la cuenta
    # ------------------------------------------------------------------
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)  # acceso al admin de Django

    # ------------------------------------------------------------------
    # Auditoría
    # ------------------------------------------------------------------
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    objects = UserManager()

    # Email como campo de autenticación en lugar de username
    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name        = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    # ------------------------------------------------------------------
    # Helpers de rol — evitan comparar strings hardcodeados en el código
    # ------------------------------------------------------------------
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER