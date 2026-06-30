# apps/reviews/serializers.py
from rest_framework import serializers
from django.utils import timezone
from apps.reviews.models import Review
from apps.orders.models import Order, OrderItem


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer de lectura — muestra datos del autor."""
    author_name = serializers.CharField(source="user.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model  = Review
        fields = [
            "id", "product", "author_name", "rating",
            "title", "body", "status", "status_display",
            "created_at"
        ]
        read_only_fields = ["status", "created_at"]


class CreateReviewSerializer(serializers.ModelSerializer):
    """
    Serializer para crear una reseña.
    Valida que el usuario haya comprado el producto
    en una orden entregada.
    """
    class Meta:
        model  = Review
        fields = ["product", "rating", "title", "body"]

    def validate(self, attrs):
        user    = self.context["request"].user
        product = attrs["product"]

        # Verificar que el usuario compró el producto
        purchased = OrderItem.objects.filter(
            order__user=user,
            order__status=Order.Status.DELIVERED,
            variant__product=product
        ).exists()

        if not purchased:
            raise serializers.ValidationError({
                "product": "Solo podés reseñar productos que hayas comprado y recibido."
            })

        # Verificar que no haya reseñado antes
        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError({
                "product": "Ya escribiste una reseña para este producto."
            })

        # Guardar la orden relacionada
        order = Order.objects.filter(
            user=user,
            status=Order.Status.DELIVERED,
            items__variant__product=product
        ).first()
        attrs["order"] = order

        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ModerateReviewSerializer(serializers.Serializer):
    """Solo admins — aprobar o rechazar reseñas."""
    action        = serializers.ChoiceField(choices=["approve", "reject"])
    reject_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["action"] == "reject" and not attrs.get("reject_reason"):
            raise serializers.ValidationError({
                "reject_reason": "Debés indicar el motivo del rechazo."
            })
        return attrs


class ProductRatingSerializer(serializers.Serializer):
    """Resumen de rating de un producto."""
    average_rating = serializers.FloatField()
    total_reviews  = serializers.IntegerField()
    rating_breakdown = serializers.DictField()