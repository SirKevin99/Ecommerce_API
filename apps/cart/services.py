# apps/cart/services.py
from django.db import transaction
from apps.cart.models import Cart, CartItem
from apps.products.models import ProductVariant
from apps.users.models import User


class CartService:

    @staticmethod
    def get_or_create_cart(user: User) -> Cart:
        """
        Obtiene el carrito del usuario o lo crea si no existe.
        get_or_create retorna una tupla (objeto, created).
        """
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    @staticmethod
    @transaction.atomic
    def add_item(user: User, variant: ProductVariant, quantity: int) -> CartItem:
        """
        Agrega un ítem al carrito.
        Si la variante ya existe en el carrito, suma la cantidad.
        Verifica stock antes de actualizar para evitar sobreventa.
        """
        cart = CartService.get_or_create_cart(user)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={"quantity": quantity}
        )

        if not created:
            # La variante ya estaba en el carrito — sumar cantidad
            new_quantity = item.quantity + quantity

            # Verificar que el stock aguante la nueva cantidad total
            if variant.stock < new_quantity:
                raise ValueError(
                    f"Stock insuficiente. Disponible: {variant.stock}, "
                    f"en carrito: {item.quantity}, solicitado adicional: {quantity}."
                )
            item.quantity = new_quantity
            item.save(update_fields=["quantity"])

        return item

    @staticmethod
    @transaction.atomic
    def update_item(cart_item: CartItem, quantity: int) -> CartItem:
        """
        Actualiza la cantidad de un ítem existente.
        """
        cart_item.quantity = quantity
        cart_item.save(update_fields=["quantity"])
        return cart_item

    @staticmethod
    def remove_item(cart_item: CartItem) -> None:
        """Elimina un ítem específico del carrito."""
        cart_item.delete()

    @staticmethod
    def clear_cart(user: User) -> None:
        """Vacía el carrito completo — usado al confirmar una orden."""
        cart = CartService.get_or_create_cart(user)
        cart.clear()