# apps/cart/models.py
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User
from apps.products.models import ProductVariant


# ==============================================================================
# CARRITO
# ==============================================================================

class Cart(models.Model):
    """
    Carrito de compras vinculado a un usuario.
    Un usuario solo puede tener un carrito activo a la vez.
    La relación OneToOne garantiza esto a nivel de base de datos.

    Por qué no guardar el carrito en sesión o caché:
    - Persiste entre dispositivos y sesiones
    - Permite recuperar el carrito si el usuario cierra el navegador
    - Facilita análisis de carritos abandonados
    """
    user       = models.OneToOneField(
                   User,
                   on_delete=models.CASCADE,
                   related_name="cart"
                 )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Carrito"
        verbose_name_plural = "Carritos"

    def __str__(self):
        return f"Carrito de {self.user.full_name}"

    @property
    def total_items(self):
        """Cantidad total de ítems (suma de quantities)."""
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        """Subtotal sin descuentos."""
        return sum(item.subtotal for item in self.items.all())

    def clear(self):
        """Vacía el carrito — se llama después de crear una orden."""
        self.items.all().delete()


# ==============================================================================
# ÍTEM DEL CARRITO
# ==============================================================================

class CartItem(models.Model):
    """
    Cada línea del carrito representa una variante con su cantidad.
    La combinación cart + variant debe ser única —
    no puede haber dos líneas para la misma variante en el mismo carrito.
    Si el usuario agrega la misma variante de nuevo, se incrementa quantity.
    """
    cart      = models.ForeignKey(
                  Cart,
                  on_delete=models.CASCADE,
                  related_name="items"
                )
    variant   = models.ForeignKey(
                  ProductVariant,
                  on_delete=models.CASCADE,
                  related_name="cart_items"
                )
    quantity  = models.PositiveIntegerField(
                  default=1,
                  validators=[MinValueValidator(1)]
                )
    added_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Ítem de Carrito"
        verbose_name_plural = "Ítems de Carrito"
        unique_together     = ("cart", "variant")  # clave de integridad

    def __str__(self):
        return f"{self.quantity}x {self.variant.sku} en carrito de {self.cart.user.full_name}"

    @property
    def subtotal(self):
        """Precio de esta línea = precio variante × cantidad."""
        return self.variant.price * self.quantity