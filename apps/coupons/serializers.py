# apps/coupons/serializers.py
from rest_framework import serializers
from django.utils import timezone
from apps.coupons.models import Coupon, CouponUsage


class CouponSerializer(serializers.ModelSerializer):
    """Serializer completo para administración de cupones."""
    is_fully_valid   = serializers.BooleanField(read_only=True)
    uses_remaining   = serializers.SerializerMethodField()

    class Meta:
        model  = Coupon
        fields = [
            "id", "code", "description", "discount_type",
            "discount_value", "max_discount_amount",
            "minimum_order_amount", "valid_from", "valid_until",
            "max_uses", "current_uses", "uses_remaining",
            "max_uses_per_user", "is_active", "is_fully_valid",
            "created_at"
        ]
        read_only_fields = ["current_uses", "created_at"]

    def get_uses_remaining(self, obj):
        if obj.max_uses is None:
            return None  # ilimitado
        return max(0, obj.max_uses - obj.current_uses)

    def validate(self, attrs):
        valid_from  = attrs.get("valid_from")
        valid_until = attrs.get("valid_until")

        if valid_from and valid_until and valid_from >= valid_until:
            raise serializers.ValidationError({
                "valid_until": "La fecha de fin debe ser posterior a la fecha de inicio."
            })

        # Validar que descuento porcentual no supere 100%
        if (attrs.get("discount_type") == Coupon.DiscountType.PERCENTAGE
                and attrs.get("discount_value", 0) > 100):
            raise serializers.ValidationError({
                "discount_value": "El descuento porcentual no puede superar el 100%."
            })

        return attrs


class ApplyCouponSerializer(serializers.Serializer):
    """
    Serializer para que el usuario aplique un cupón al carrito.
    Valida el código y el monto mínimo de orden.
    """
    code         = serializers.CharField(max_length=50)
    order_amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, attrs):
        code         = attrs["code"].upper().strip()
        order_amount = attrs["order_amount"]
        user         = self.context["request"].user

        # Verificar que el cupón existe
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({"code": "Cupón no válido."})

        # Verificar validez completa
        if not coupon.is_active:
            raise serializers.ValidationError({"code": "Este cupón está desactivado."})

        if not coupon.is_valid_date:
            raise serializers.ValidationError({"code": "Este cupón está vencido o aún no es válido."})

        if not coupon.is_usage_available:
            raise serializers.ValidationError({"code": "Este cupón ha alcanzado su límite de usos."})

        # Verificar monto mínimo
        if order_amount < coupon.minimum_order_amount:
            raise serializers.ValidationError({
                "code": f"El monto mínimo para este cupón es {coupon.minimum_order_amount}."
            })

        # Verificar usos por usuario
        user_uses = CouponUsage.objects.filter(coupon=coupon, user=user).count()
        if user_uses >= coupon.max_uses_per_user:
            raise serializers.ValidationError({
                "code": "Ya usaste este cupón el máximo de veces permitido."
            })

        attrs["coupon"] = coupon
        return attrs


class CouponPreviewSerializer(serializers.Serializer):
    """
    Respuesta al aplicar un cupón — muestra el descuento calculado.
    """
    code              = serializers.CharField()
    discount_type     = serializers.CharField()
    discount_value    = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount   = serializers.DecimalField(max_digits=10, decimal_places=2)
    original_amount   = serializers.DecimalField(max_digits=10, decimal_places=2)
    final_amount      = serializers.DecimalField(max_digits=10, decimal_places=2)