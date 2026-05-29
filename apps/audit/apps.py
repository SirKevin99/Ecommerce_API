# apps/audit/apps.py
from django.apps import AppConfig

class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # El name debe reflejar la ruta completa desde la raíz del proyecto
    name = "apps.audit"