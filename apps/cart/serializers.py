# apps/cart/serializers.py
from rest_framework import serializers
from apps.cart.models import Cart, CartItem
from apps.products.models import ProductVariant


class CartItemProductSerializer(serializers.Serializer):
    """
    Datos del producto que se muestran dentro de cada ítem del carrito.
    Serializer plano para evitar queries innecesarias.
    """
    product_name  = serializers.CharField(source="variant.product.name")
    variant_sku   = serializers.CharField(source="variant.sku")
    price         = serializers.DecimalField(
                      source="variant.price",
                      max_digits=10,
                      decimal_places=2
                    )
    stock         = serializers.IntegerField(source="variant.stock")
    attributes    = serializers.SerializerMethodField()

    def get_attributes(self, obj):
        return [
            {"attribute": av.attribute.name, "value": av.value}
            for av in obj.variant.attributes.all()
        ]


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer completo de un ítem — incluye datos del producto
    y el subtotal calculado.
    """
    product_info = CartItemProductSerializer(source="*", read_only=True)
    subtotal     = serializers.DecimalField(
                     max_digits=10,
                     decimal_places=2,
                     read_only=True
                   )

    class Meta:
        model  = CartItem
        fields = ["id", "variant", "quantity", "product_info", "subtotal", "added_at"]
        read_only_fields = ["added_at"]


class AddToCartSerializer(serializers.Serializer):
    """
    Serializer para agregar un ítem al carrito.
    Valida que la variante exista, esté activa y tenga stock suficiente.
    """
    variant_id = serializers.IntegerField()
    quantity   = serializers.IntegerField(min_value=1)

    def validate_variant_id(self, value):
        try:
            variant = ProductVariant.objects.get(id=value, is_active=True)
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError("La variante no existe o no está disponible.")
        return value

    def validate(self, attrs):
        variant_id = attrs["variant_id"]
        quantity   = attrs["quantity"]

        variant = ProductVariant.objects.get(id=variant_id)

        if variant.stock < quantity:
            raise serializers.ValidationError({
                "quantity": f"Stock insuficiente. Disponible: {variant.stock}."
            })

        attrs["variant"] = variant
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    """
    Serializer para actualizar la cantidad de un ítem existente.
    """
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        quantity = attrs["quantity"]
        # self.instance es el CartItem que se está actualizando
        variant  = self.instance.variant

        if variant.stock < quantity:
            raise serializers.ValidationError({
                "quantity": f"Stock insuficiente. Disponible: {variant.stock}."
            })
        return attrs


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer completo del carrito con todos sus ítems,
    subtotal y cantidad total.
    """
    items       = CartItemSerializer(many=True, read_only=True)
    subtotal    = serializers.DecimalField(
                    max_digits=10,
                    decimal_places=2,
                    read_only=True
                  )
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Cart
        fields = ["id", "items", "total_items", "subtotal", "updated_at"]