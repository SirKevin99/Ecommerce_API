# apps/coupons/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.users.models import User


# ==============================================================================
# CUPÓN
# ==============================================================================

class Coupon(models.Model):
    """
    Cupón de descuento con dos tipos posibles:
    - PERCENTAGE: descuento porcentual (ej: 20% off)
    - FIXED:      descuento de monto fijo (ej: $10 off)

    Por qué separar en tipos y no tener dos campos opcionales:
    - Evita ambigüedad — siempre queda claro cómo se calcula
    - Facilita agregar nuevos tipos en el futuro sin romper la lógica
    """

    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "Porcentaje"
        FIXED      = "fixed",      "Monto fijo"

    code             = models.CharField(max_length=50, unique=True)
    description      = models.TextField(blank=True)
    discount_type    = models.CharField(
                         max_length=20,
                         choices=DiscountType.choices,
                         default=DiscountType.PERCENTAGE
                       )
    discount_value   = models.DecimalField(
                         max_digits=10,
                         decimal_places=2,
                         validators=[MinValueValidator(0)]
                       )

    # Límite del descuento porcentual — evita descuentos del 100%
    max_discount_amount = models.DecimalField(
                            max_digits=10,
                            decimal_places=2,
                            null=True,
                            blank=True,
                            help_text="Monto máximo de descuento (solo para tipo porcentaje)"
                          )

    # Monto mínimo de compra para usar el cupón
    minimum_order_amount = models.DecimalField(
                             max_digits=10,
                             decimal_places=2,
                             default=0,
                             validators=[MinValueValidator(0)]
                           )

    # Control de validez temporal
    valid_from   = models.DateTimeField()
    valid_until  = models.DateTimeField()

    # Control de usos
    max_uses     = models.PositiveIntegerField(
                     null=True,
                     blank=True,
                     help_text="Dejar vacío para usos ilimitados"
                   )
    current_uses = models.PositiveIntegerField(default=0)

    # Control de usos por usuario
    max_uses_per_user = models.PositiveIntegerField(
                          default=1,
                          help_text="Cuántas veces puede usar este cupón el mismo usuario"
                        )

    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    created_by   = models.ForeignKey(
                     User,
                     on_delete=models.SET_NULL,
                     null=True,
                     related_name="coupons_created"
                   )

    class Meta:
        verbose_name        = "Cupón"
        verbose_name_plural = "Cupones"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.code} — {self.get_discount_type_display()}: {self.discount_value}"

    # ------------------------------------------------------------------
    # Validaciones de negocio
    # ------------------------------------------------------------------

    @property
    def is_valid_date(self) -> bool:
        """Verifica que el cupón esté dentro del período de validez."""
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until

    @property
    def is_usage_available(self) -> bool:
        """Verifica que el cupón no haya superado su límite de usos."""
        if self.max_uses is None:
            return True
        return self.current_uses < self.max_uses

    @property
    def is_fully_valid(self) -> bool:
        """Validación completa — activo, dentro de fecha y con usos disponibles."""
        return self.is_active and self.is_valid_date and self.is_usage_available

    def calculate_discount(self, order_amount) -> "decimal":
        """
        Calcula el monto de descuento para un total de orden dado.
        Nunca retorna un descuento mayor al total de la orden.
        """
        from decimal import Decimal

        if self.discount_type == self.DiscountType.FIXED:
            discount = min(self.discount_value, order_amount)

        else:  # PERCENTAGE
            discount = order_amount * (self.discount_value / Decimal("100"))

            # Aplicar límite máximo de descuento si está definido
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)

        return discount.quantize(Decimal("0.01"))

    def increment_uses(self) -> None:
        """
        Incrementa el contador de usos de forma segura.
        Se llama al confirmar una orden con este cupón.
        """
        self.current_uses += 1
        self.save(update_fields=["current_uses"])


# ==============================================================================
# USO DE CUPÓN POR USUARIO
# ==============================================================================

class CouponUsage(models.Model):
    """
    Registro de cada uso de un cupón por usuario.
    Permite controlar max_uses_per_user y auditar el historial.
    """
    coupon     = models.ForeignKey(
                   Coupon,
                   on_delete=models.CASCADE,
                   related_name="usages"
                 )
    user       = models.ForeignKey(
                   User,
                   on_delete=models.CASCADE,
                   related_name="coupon_usages"
                 )
    used_at    = models.DateTimeField(auto_now_add=True)
    order_id   = models.PositiveIntegerField(
                   null=True,
                   blank=True,
                   help_text="ID de la orden donde se usó este cupón"
                 )

    class Meta:
        verbose_name        = "Uso de Cupón"
        verbose_name_plural = "Usos de Cupón"
        ordering            = ["-used_at"]

    def __str__(self):
        return f"{self.user.email} usó {self.coupon.code} el {self.used_at:%Y-%m-%d}"