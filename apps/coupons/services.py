# apps/coupons/services.py
from decimal import Decimal
from apps.coupons.models import Coupon, CouponUsage
from apps.users.models import User


class CouponService:

    @staticmethod
    def apply_coupon(coupon: Coupon, order_amount: Decimal) -> dict:
        """
        Calcula el descuento y retorna el resumen para mostrar al usuario
        antes de confirmar la orden.
        """
        discount_amount = coupon.calculate_discount(order_amount)
        final_amount    = max(order_amount - discount_amount, Decimal("0.00"))

        return {
            "code":            coupon.code,
            "discount_type":   coupon.discount_type,
            "discount_value":  coupon.discount_value,
            "discount_amount": discount_amount,
            "original_amount": order_amount,
            "final_amount":    final_amount,
        }

    @staticmethod
    def register_coupon_usage(coupon: Coupon, user: User, order_id: int = None) -> None:
        """
        Registra el uso de un cupón al confirmar una orden.
        Incrementa el contador global y crea el registro por usuario.
        Se llama desde OrderService al crear la orden.
        """
        CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            order_id=order_id
        )
        coupon.increment_uses()

    @staticmethod
    def get_coupon_by_code(code: str) -> Coupon:
        """
        Obtiene un cupón por código (case-insensitive).
        Lanza Coupon.DoesNotExist si no existe.
        """
        return Coupon.objects.get(code=code.upper().strip())