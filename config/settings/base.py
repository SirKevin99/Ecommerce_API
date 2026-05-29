# config/settings/base.py
import environ
from pathlib import Path

# ==============================================================================
# RUTAS BASE
# ==============================================================================

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR apunta a la raíz del proyecto (donde está manage.py)
# .parent.parent porque base.py está en config/settings/, dos niveles adentro
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ==============================================================================
# LECTURA DE VARIABLES DE ENTORNO
# ==============================================================================

# django-environ permite leer el archivo .env de forma segura
# Nunca hardcodees credenciales en settings — siempre desde .env
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# ==============================================================================
# SEGURIDAD
# ==============================================================================

SECRET_KEY = env("SECRET_KEY")

# ==============================================================================
# APLICACIONES INSTALADAS
# ==============================================================================

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  # para logout con JWT
    "django_filters",
    "drf_spectacular",
    "django_extensions",
]

LOCAL_APPS = [
    "apps.users",
    "apps.products",
    "apps.orders",
    "apps.cart",
    "apps.reviews",
    "apps.coupons",
    "apps.billing",
    "apps.audit",
]

# Separar en tres listas tiene una razón clara:
# - facilita saber qué es nativo, qué es externo y qué es nuestro
# - permite deshabilitar grupos enteros fácilmente
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ==============================================================================
# URLS Y WSGI
# ==============================================================================

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# ==============================================================================
# TEMPLATES
# ==============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ==============================================================================
# BASE DE DATOS
# ==============================================================================

# django-environ parsea automáticamente la URL de conexión
# Formato: postgres://usuario:password@host:puerto/nombre_db
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": "127.0.0.1",
        "PORT": "5433",
    }
}
# ==============================================================================
# MODELO DE USUARIO PERSONALIZADO
# ==============================================================================

# Apuntar a nuestro modelo custom desde el inicio es CRÍTICO.
# Si lo cambiás después de crear migraciones, tenés que resetear toda la DB.
# Siempre definir esto antes del primer makemigrations.
AUTH_USER_MODEL = "users.User"

# ==============================================================================
# VALIDACIÓN DE CONTRASEÑAS
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==============================================================================
# INTERNACIONALIZACIÓN
# ==============================================================================

LANGUAGE_CODE = "es-py"
TIME_ZONE = "America/Asuncion"
USE_I18N = True
USE_TZ = True  # Siempre True — almacena fechas en UTC, convierte al mostrar

# ==============================================================================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ==============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"  # imágenes de productos, etc.

# ==============================================================================
# PRIMARY KEY DEFAULT
# ==============================================================================

# BigAutoField para evitar overflow en tablas con muchos registros
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# DJANGO REST FRAMEWORK
# ==============================================================================

REST_FRAMEWORK = {
    # JWT como método de autenticación por defecto
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Solo usuarios autenticados pueden acceder por defecto
    # Los endpoints públicos (login, register) lo sobreescriben explícitamente
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    # Paginación global — todos los listados usan esto salvo que se sobreescriba
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Filtrado, búsqueda y ordenamiento disponibles en todas las vistas
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # Documentación automática con drf-spectacular
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Formato de respuesta siempre JSON
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
}

# ==============================================================================
# JWT — SIMPLE JWT
# ==============================================================================

from datetime import timedelta

SIMPLE_JWT = {
    # Access token corto por seguridad — si es robado, expira pronto
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    # Refresh token largo — el usuario no tiene que re-loguearse seguido
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Genera un nuevo refresh token en cada uso (mejor seguridad)
    "ROTATE_REFRESH_TOKENS": True,
    # Invalida el refresh token anterior al rotar (requiere token_blacklist)
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# ==============================================================================
# DRF SPECTACULAR — DOCUMENTACIÓN OPENAPI
# ==============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "E-commerce API",
    "DESCRIPTION": "API REST profesional para plataforma de E-commerce",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}