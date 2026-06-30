# apps/products/serializers.py
from rest_framework import serializers
from apps.products.models import (
    Category, Product, ProductImage,
    Attribute, AttributeValue, ProductVariant
)


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ["id", "name", "slug", "description", "parent", "children", "is_active"]

    def get_children(self, obj):
        # Solo incluir hijos en el nivel raíz para evitar recursión infinita
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)

    class Meta:
        model  = AttributeValue
        fields = ["id", "attribute_name", "value"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ["id", "image", "alt_text", "is_primary", "order"]


class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = AttributeValueSerializer(many=True, read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model  = ProductVariant
        fields = [
            "id", "sku", "price", "stock",
            "attributes", "is_active", "is_in_stock"
        ]


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer liviano para listados — no incluye variantes completas.
    Minimiza la cantidad de datos transferidos en listados grandes.
    """
    category_name = serializers.CharField(source="category.name", read_only=True)
    min_price     = serializers.DecimalField(
                      max_digits=10, decimal_places=2, read_only=True
                    )
    total_stock   = serializers.IntegerField(read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            "id", "name", "slug", "category_name",
            "brand", "min_price", "total_stock",
            "is_active", "primary_image"
        ]

    def get_primary_image(self, obj):
        image = obj.images.filter(is_primary=True).first()
        if image:
            request = self.context.get("request")
            return request.build_absolute_uri(image.image.url) if request else None
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el detalle de un producto.
    Incluye variantes e imágenes.
    """
    category  = CategorySerializer(read_only=True)
    variants  = ProductVariantSerializer(many=True, read_only=True)
    images    = ProductImageSerializer(many=True, read_only=True)
    min_price   = serializers.DecimalField(
                    max_digits=10, decimal_places=2, read_only=True
                  )
    total_stock = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Product
        fields = [
            "id", "name", "slug", "description", "category",
            "brand", "min_price", "total_stock", "is_in_stock",
            "variants", "images", "is_active", "created_at"
        ]


class ProductWriteSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar productos.
    Separado del de lectura para tener control total sobre
    qué campos son escriturables.
    """
    class Meta:
        model  = Product
        fields = [
            "name", "slug", "description",
            "category", "brand", "is_active"
        ]

    def create(self, validated_data):
        # El usuario que crea el producto se toma del request
        request = self.context.get("request")
        validated_data["created_by"] = request.user
        return super().create(validated_data)