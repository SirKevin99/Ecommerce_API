# apps/audit/services.py
from django.contrib.contenttypes.models import ContentType
from apps.audit.models import AuditLog
from apps.users.models import User


class AuditService:

    @staticmethod
    def log(
        action: str,
        user: User = None,
        instance=None,
        changes: dict = None,
        request=None,
        object_repr: str = ""
    ) -> AuditLog:
        """
        Registra una acción en el log de auditoría.

        Uso desde cualquier service:
            AuditService.log(
                action=AuditLog.Action.UPDATE,
                user=request.user,
                instance=product,
                changes={"price": {"before": 100, "after": 120}},
                request=request
            )
        """
        content_type = None
        object_id    = None

        if instance:
            content_type = ContentType.objects.get_for_model(instance)
            object_id    = instance.pk
            object_repr  = object_repr or str(instance)

        ip_address = None
        user_agent = ""

        if request:
            ip_address = AuditService._get_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

        return AuditLog.objects.create(
            user         = user,
            action       = action,
            content_type = content_type,
            object_id    = object_id,
            object_repr  = object_repr,
            changes      = changes or {},
            ip_address   = ip_address,
            user_agent   = user_agent,
        )

    @staticmethod
    def log_login(user: User, request) -> AuditLog:
        return AuditService.log(
            action      = AuditLog.Action.LOGIN,
            user        = user,
            request     = request,
            object_repr = f"Login: {user.email}"
        )

    @staticmethod
    def log_order_created(order, user: User, request=None) -> AuditLog:
        return AuditService.log(
            action      = AuditLog.Action.CREATE,
            user        = user,
            instance    = order,
            request     = request,
            object_repr = str(order),
            changes     = {"total": {"after": str(order.total)}}
        )

    @staticmethod
    def _get_ip(request) -> str:
        """Obtiene la IP real considerando proxies."""
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")