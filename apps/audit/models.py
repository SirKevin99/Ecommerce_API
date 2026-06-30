# apps/audit/models.py
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from apps.users.models import User


class AuditLog(models.Model):
    """
    Registro de auditoría genérico para cualquier modelo.

    Usa GenericForeignKey para poder auditar cualquier objeto
    sin crear una tabla de auditoría por cada modelo.

    Registra: quién hizo qué, en qué objeto, cuándo y qué cambió.
    """

    class Action(models.TextChoices):
        CREATE = "create", "Creación"
        UPDATE = "update", "Modificación"
        DELETE = "delete", "Eliminación"
        LOGIN  = "login",  "Inicio de sesión"
        LOGOUT = "logout", "Cierre de sesión"

    # Quién realizó la acción
    user         = models.ForeignKey(
                     User,
                     on_delete=models.SET_NULL,
                     null=True,
                     blank=True,
                     related_name="audit_logs"
                   )

    # Qué acción realizó
    action       = models.CharField(max_length=20, choices=Action.choices)

    # Sobre qué objeto (genérico — funciona con cualquier modelo)
    content_type  = models.ForeignKey(
                      ContentType,
                      on_delete=models.SET_NULL,
                      null=True,
                      blank=True
                    )
    object_id     = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    object_repr   = models.CharField(
                      max_length=255,
                      blank=True,
                      help_text="Representación textual del objeto al momento del log"
                    )

    # Qué cambió — guardamos JSON con los campos antes y después
    changes      = models.JSONField(
                     default=dict,
                     blank=True,
                     help_text="{'campo': {'before': valor_anterior, 'after': valor_nuevo}}"
                   )

    # Contexto de la request
    ip_address   = models.GenericIPAddressField(null=True, blank=True)
    user_agent   = models.CharField(max_length=255, blank=True)

    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering            = ["-created_at"]
        indexes             = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else "Sistema"
        return f"[{self.get_action_display()}] {user_str} — {self.object_repr} ({self.created_at:%Y-%m-%d %H:%M})"