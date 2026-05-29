# config/settings/development.py
from .base import *  # noqa

# ==============================================================================
# SEGURIDAD — DESARROLLO
# ==============================================================================

DEBUG = True

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ==============================================================================
# APPS SOLO EN DESARROLLO
# ==============================================================================



# ==============================================================================
# EMAILS EN DESARROLLO
# ==============================================================================

# Imprime los emails en consola en vez de enviarlos realmente
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ==============================================================================
# DEBUG TOOLBAR (opcional, recomendado)
# ==============================================================================

# Mostrar queries SQL en desarrollo es clave para detectar N+1 queries
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",  # muestra cada query SQL ejecutada
        },
    },
}