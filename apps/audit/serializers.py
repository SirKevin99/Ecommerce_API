# apps/audit/serializers.py
from rest_framework import serializers
from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email    = serializers.EmailField(source="user.email",           read_only=True)
    action_display = serializers.CharField(source="get_action_display",   read_only=True)
    model_name    = serializers.CharField(source="content_type.model",    read_only=True)

    class Meta:
        model  = AuditLog
        fields = [
            "id", "user_email", "action", "action_display",
            "model_name", "object_id", "object_repr",
            "changes", "ip_address", "created_at"
        ]