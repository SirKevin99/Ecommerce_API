# apps/orders/serializers.py
from rest_framework import serializers
from apps.orders.models import Order, OrderItem, OrderStatusHistory


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OrderItem
        fields = [
            "id", "variant", "product_name",
            "variant_sku", "unit_price", "quantity", "subtotal"
        ]
        read_only_fields = fields


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(
                         source="changed_by.email",
                         read_only=True
                       )
    status_display   = serializers.CharField(
                         source="get_status_display",
                         read_only=True
                       )

    class Meta:
        model  = OrderStatusHistory
        fields = ["id", "status", "status_display", "changed_by_email", "note", "changed_at"]


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer liviano para el historial de órdenes."""
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    items_count    = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Order
        fields = [
            "id", "status", "status_display", "subtotal",
            "discount_amount", "total", "items_count",
            "coupon_code", "created_at"
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer completo con ítems e historial de estados."""
    items          = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    items_count    = serializers.IntegerField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Order
        fields = [
            "id", "status", "status_display", "can_be_cancelled",
            "shipping_address", "shipping_city", "shipping_country",
            "subtotal", "discount_amount", "total",
            "coupon_code", "notes", "items_count",
            "items", "status_history", "created_at", "updated_at"
        ]


class CreateOrderSerializer(serializers.Serializer):
    """
    Serializer para crear una orden desde el carrito.
    El usuario solo provee dirección de envío, cupón y notas.
    El resto se calcula desde el carrito.
    """
    shipping_address = serializers.CharField()
    shipping_city    = serializers.CharField(max_length=100)
    shipping_country = serializers.CharField(max_length=100)
    coupon_code      = serializers.CharField(max_length=50, required=False, allow_blank=True)
    notes            = serializers.TextField(required=False, allow_blank=True)

    def validate_coupon_code(self, value):
        if not value:
            return value
        from apps.coupons.models import Coupon
        try:
            coupon = Coupon.objects.get(code=value.upper().strip())
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Cupón no válido.")
        if not coupon.is_fully_valid:
            raise serializers.ValidationError("Este cupón no está disponible.")
        return value.upper().strip()


class UpdateOrderStatusSerializer(serializers.Serializer):
    """Solo admins pueden cambiar el estado de una orden."""
    status = serializers.ChoiceField(choices=Order.Status.choices)
    note   = serializers.CharField(required=False, allow_blank=True)