# apps/products/services.py
from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.products.models import Product, ProductVariant, AttributeValue


class ProductService:

    @staticmethod
    @transaction.atomic
    def create_variant(product_id: int, data: dict) -> ProductVariant:
        """
        Crea una variante y le asigna sus atributos.
        transaction.atomic garantiza que si algo falla,
        no quede una variante a medio crear en la DB.
        """
        product         = get_object_or_404(Product, id=product_id)
        attribute_ids   = data.pop("attribute_ids", [])

        variant         = ProductVariant.objects.create(product=product, **data)

        if attribute_ids:
            attributes  = AttributeValue.objects.filter(id__in=attribute_ids)
            variant.attributes.set(attributes)

        return variant

    @staticmethod
    @transaction.atomic
    def update_stock(variant_id: int, quantity: int, operation: str) -> ProductVariant:
        """
        Actualiza el stock de una variante.
        operation: 'add' para sumar, 'subtract' para restar.
        Usar select_for_update() evita condiciones de carrera
        cuando múltiples requests intentan modificar el mismo stock.
        """
        variant = ProductVariant.objects.select_for_update().get(id=variant_id)

        if operation == "subtract":
            variant.reduce_stock(quantity)
        elif operation == "add":
            variant.restore_stock(quantity)
        else:
            raise ValueError(f"Operación inválida: {operation}")

        return variant