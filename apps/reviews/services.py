# apps/reviews/services.py
from django.utils import timezone
from django.db.models import Avg, Count
from apps.reviews.models import Review
from apps.users.models import User


class ReviewService:

    @staticmethod
    def moderate_review(review: Review, action: str, admin: User, reason: str = "") -> Review:
        """Aprueba o rechaza una reseña."""
        if action == "approve":
            review.status = Review.Status.APPROVED
        else:
            review.status       = Review.Status.REJECTED
            review.reject_reason = reason

        review.moderated_by = admin
        review.moderated_at = timezone.now()
        review.save()
        return review

    @staticmethod
    def get_product_rating_summary(product_id: int) -> dict:
        """
        Calcula el resumen de rating de un producto.
        Incluye promedio y desglose por cantidad de estrellas.
        """
        reviews = Review.objects.filter(
            product_id=product_id,
            status=Review.Status.APPROVED
        )
        total   = reviews.count()
        average = reviews.aggregate(avg=Avg("rating"))["avg"] or 0

        # Desglose: cuántas reseñas tiene cada puntaje
        breakdown = {}
        for star in range(1, 6):
            count = reviews.filter(rating=star).count()
            breakdown[f"{star}_stars"] = {
                "count":      count,
                "percentage": round((count / total * 100), 1) if total > 0 else 0
            }

        return {
            "average_rating":  round(average, 1),
            "total_reviews":   total,
            "rating_breakdown": breakdown,
        }