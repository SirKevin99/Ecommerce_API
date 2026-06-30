# apps/reviews/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import User
from apps.products.models import Product
from apps.orders.models import Order


class Review(models.Model):
    """
    Reseña de un producto por un usuario.

    Reglas de negocio:
    - Un usuario solo puede reseñar un producto una vez
    - Solo puede reseñar productos que compró y fueron entregados
    - El rating va de 1 a 5 estrellas
    - Las reseñas pueden ser moderadas por un admin antes de publicarse
    """

    class Status(models.TextChoices):
        PENDING  = "pending",  "Pendiente de moderación"
        APPROVED = "approved", "Aprobada"
        REJECTED = "rejected", "Rechazada"

    product    = models.ForeignKey(
                   Product,
                   on_delete=models.CASCADE,
                   related_name="reviews"
                 )
    user       = models.ForeignKey(
                   User,
                   on_delete=models.CASCADE,
                   related_name="reviews"
                 )
    order      = models.ForeignKey(
                   Order,
                   on_delete=models.SET_NULL,
                   null=True,
                   related_name="reviews",
                   help_text="Orden desde la cual se compró el producto"
                 )
    rating     = models.PositiveSmallIntegerField(
                   validators=[MinValueValidator(1), MaxValueValidator(5)]
                 )
    title      = models.CharField(max_length=150, blank=True)
    body       = models.TextField(blank=True)
    status     = models.CharField(
                   max_length=20,
                   choices=Status.choices,
                   default=Status.PENDING
                 )

    # Moderación
    moderated_by = models.ForeignKey(
                     User,
                     on_delete=models.SET_NULL,
                     null=True,
                     blank=True,
                     related_name="moderated_reviews"
                   )
    moderated_at = models.DateTimeField(null=True, blank=True)
    reject_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Reseña"
        verbose_name_plural = "Reseñas"
        ordering            = ["-created_at"]
        # Un usuario solo puede reseñar un producto una vez
        unique_together     = ("product", "user")

    def __str__(self):
        return f"{self.user.email} — {self.product.name} — {self.rating}★"