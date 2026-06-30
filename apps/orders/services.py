# apps/orders/services.py
from decimal import Decimal
from django.db import transaction
from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.cart.models import Cart
from apps.coupons.models import Coupon
from apps.coupons.services import CouponService
from apps.users.models import User


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(user: User, data: dict) -> Order:
        """
        Crea una orden completa desde el carrito del usuario.

        Pasos en orden:
        1. Obtener y validar el carrito
        2. Validar stock de cada variante
        3. Calcular subtotal
        4. Aplicar cupón si existe
        5. Crear la orden y sus ítems
        6. Reducir stock de cada variante
        7. Registrar uso del cupón
        8. Vaciar el carrito
        9. Registrar estado inicial en historial

        Todo dentro de transaction.atomic — si cualquier paso falla,
        se revierte todo y no queda nada a medio crear.
        """

        # PASO 1 — Obtener carrito
        try:
            cart = Cart.objects.prefetch_related(
                "items__variant__product"
            ).get(user=user)
        except Cart.DoesNotExist:
            raise ValueError("No tenés un carrito activo.")

        if not cart.items.exists():
            raise ValueError("El carrito está vacío.")

        # PASO 2 — Validar stock antes de crear la orden
        for item in cart.items.all():
            if item.variant.stock < item.quantity:
                raise ValueError(
                    f"Stock insuficiente para '{item.variant.product.name}' "
                    f"(SKU: {item.variant.sku}). "
                    f"Disponible: {item.variant.stock}, solicitado: {item.quantity}."
                )

        # PASO 3 — Calcular subtotal
        subtotal = sum(item.subtotal for item in cart.items.all())

        # PASO 4 — Aplicar cupón si existe
        discount_amount = Decimal("0.00")
        coupon          = None
        coupon_code     = data.get("coupon_code", "")

        if coupon_code:
            coupon          = Coupon.objects.get(code=coupon_code)
            discount_amount = coupon.calculate_discount(subtotal)

            # Verificar uso por usuario
            from apps.coupons.models import CouponUsage
            user_uses = CouponUsage.objects.filter(coupon=coupon, user=user).count()
            if user_uses >= coupon.max_uses_per_user:
                raise ValueError("Ya usaste este cupón el máximo de veces permitido.")

        total = max(subtotal - discount_amount, Decimal("0.00"))

        # PASO 5 — Crear la orden
        order = Order.objects.create(
            user             = user,
            status           = Order.Status.PENDING,
            shipping_address = data["shipping_address"],
            shipping_city    = data["shipping_city"],
            shipping_country = data["shipping_country"],
            notes            = data.get("notes", ""),
            subtotal         = subtotal,
            discount_amount  = discount_amount,
            total            = total,
            coupon           = coupon,
            coupon_code      = coupon_code,
        )

        # PASO 5b — Crear ítems de la orden (snapshot)
        for item in cart.items.all():
            OrderItem.objects.create(
                order        = order,
                variant      = item.variant,
                product_name = item.variant.product.name,
                variant_sku  = item.variant.sku,
                unit_price   = item.variant.price,
                quantity     = item.quantity,
                subtotal     = item.subtotal,
            )

        # PASO 6 — Reducir stock
        for item in cart.items.all():
            item.variant.reduce_stock(item.quantity)

        # PASO 7 — Registrar uso del cupón
        if coupon:
            CouponService.register_coupon_usage(coupon, user, order.id)

        # PASO 8 — Vaciar carrito
        cart.clear()

        # PASO 9 — Historial de estado inicial
        OrderStatusHistory.objects.create(
            order      = order,
            status     = Order.Status.PENDING,
            changed_by = user,
            note       = "Orden creada."
        )

        return order

    @staticmethod
    @transaction.atomic
    def update_order_status(order: Order, new_status: str, changed_by: User, note: str = "") -> Order:
        """
        Cambia el estado de una orden con validación de flujo.
        Restaura stock si se cancela la orden.
        """
        # Validar transiciones permitidas
        allowed_transitions = {
            Order.Status.PENDING:   [Order.Status.CONFIRMED, Order.Status.CANCELLED],
            Order.Status.CONFIRMED: [Order.Status.SHIPPED,   Order.Status.CANCELLED],
            Order.Status.SHIPPED:   [Order.Status.DELIVERED],
            Order.Status.DELIVERED: [],
            Order.Status.CANCELLED: [],
        }

        if new_status not in allowed_transitions.get(order.status, []):
            raise ValueError(
                f"No se puede pasar de '{order.get_status_display()}' "
                f"a '{dict(Order.Status.choices)[new_status]}'."
            )

        # Restaurar stock si se cancela
        if new_status == Order.Status.CANCELLED:
            for item in order.items.all():
                item.variant.restore_stock(item.quantity)

        old_status    = order.status
        order.status  = new_status
        order.save(update_fields=["status", "updated_at"])

        # Registrar en historial
        OrderStatusHistory.objects.create(
            order      = order,
            status     = new_status,
            changed_by = changed_by,
            note       = note or f"Estado cambiado de {old_status} a {new_status}."
        )

        return order