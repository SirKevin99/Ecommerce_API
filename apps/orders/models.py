# apps/orders/models.py
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User
from apps.products.models import ProductVariant
from apps.coupons.models import Coupon


# ==============================================================================
# ORDEN
# ==============================================================================

class Order(models.Model):
    """
    Representa una orden de compra confirmada.

    Flujo de estados:
    PENDING → CONFIRMED → SHIPPED → DELIVERED
                       ↘ CANCELLED

    Por qué guardar precio/descuento en la orden y no calcularlo:
    - Los precios de productos pueden cambiar después de la compra
    - La orden debe reflejar exactamente lo que el cliente pagó
    - Es un requisito legal en facturación
    """

    class Status(models.TextChoices):
        PENDING   = "pending",   "Pendiente"
        CONFIRMED = "confirmed", "Confirmada"
        SHIPPED   = "shipped",   "Enviada"
        DELIVERED = "delivered", "Entregada"
        CANCELLED = "cancelled", "Cancelada"

    user             = models.ForeignKey(
                         User,
                         on_delete=models.PROTECT,
                         related_name="orders"
                       )

    # Estado
    status           = models.CharField(
                         max_length=20,
                         choices=Status.choices,
                         default=Status.PENDING
                       )

    # Dirección de envío — guardada como texto plano
    # para que no cambie si el usuario actualiza su perfil
    shipping_address = models.TextField()
    shipping_city    = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100)

    # Montos — siempre guardar el desglose completo
    subtotal         = models.DecimalField(
                         max_digits=10,
                         decimal_places=2,
                         validators=[MinValueValidator(0)]
                       )
    discount_amount  = models.DecimalField(
                         max_digits=10,
                         decimal_places=2,
                         default=0,
                         validators=[MinValueValidator(0)]
                       )
    total            = models.DecimalField(
                         max_digits=10,
                         decimal_places=2,
                         validators=[MinValueValidator(0)]
                       )

    # Cupón aplicado — SET_NULL para no perder la orden si se borra el cupón
    coupon           = models.ForeignKey(
                         Coupon,
                         on_delete=models.SET_NULL,
                         null=True,
                         blank=True,
                         related_name="orders"
                       )
    coupon_code      = models.CharField(max_length=50, blank=True)

    # Notas del cliente
    notes            = models.TextField(blank=True)

    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Orden"
        verbose_name_plural = "Órdenes"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"Orden #{self.id} — {self.user.email} — {self.get_status_display()}"

    @property
    def can_be_cancelled(self) -> bool:
        """Solo se puede cancelar si no fue enviada o entregada."""
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]

    @property
    def items_count(self) -> int:
        return sum(item.quantity for item in self.items.all())


# ==============================================================================
# ÍTEM DE ORDEN
# ==============================================================================

class OrderItem(models.Model):
    """
    Línea de detalle de una orden.

    Por qué guardar product_name, variant_sku y unit_price aquí:
    - Snapshot del estado del producto al momento de la compra
    - Si el producto cambia de nombre o precio, la orden histórica
      sigue mostrando los datos correctos
    - Requisito de auditoría y facturación
    """
    order        = models.ForeignKey(
                     Order,
                     on_delete=models.CASCADE,
                     related_name="items"
                   )
    variant      = models.ForeignKey(
                     ProductVariant,
                     on_delete=models.PROTECT,  # nunca borrar variante con órdenes
                     related_name="order_items"
                   )

    # Snapshot de datos al momento de la compra
    product_name = models.CharField(max_length=255)
    variant_sku  = models.CharField(max_length=100)
    unit_price   = models.DecimalField(max_digits=10, decimal_places=2)
    quantity     = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    subtotal     = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name        = "Ítem de Orden"
        verbose_name_plural = "Ítems de Orden"

    def __str__(self):
        return f"{self.quantity}x {self.variant_sku} en Orden #{self.order.id}"


# ==============================================================================
# HISTORIAL DE ESTADOS
# ==============================================================================

class OrderStatusHistory(models.Model):
    """
    Registro de cada cambio de estado de una orden.
    Permite auditar quién cambió el estado y cuándo.
    """
    order      = models.ForeignKey(
                   Order,
                   on_delete=models.CASCADE,
                   related_name="status_history"
                 )
    status     = models.CharField(max_length=20, choices=Order.Status.choices)
    changed_by = models.ForeignKey(
                   User,
                   on_delete=models.SET_NULL,
                   null=True,
                   related_name="order_status_changes"
                 )
    note       = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Historial de Estado"
        verbose_name_plural = "Historial de Estados"
        ordering            = ["-changed_at"]

    def __str__(self):
        return f"Orden #{self.order.id} → {self.status} ({self.changed_at:%Y-%m-%d %H:%M})"