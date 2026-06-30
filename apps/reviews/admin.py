# apps/reviews/admin.py
from django.contrib import admin
from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ["product", "user", "rating", "status", "created_at"]
    list_filter   = ["status", "rating"]
    search_fields = ["user__email", "product__name", "title"]
    readonly_fields = ["created_at", "updated_at", "moderated_at"]
    actions       = ["approve_reviews", "reject_reviews"]

    def approve_reviews(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status=Review.Status.APPROVED,
            moderated_by=request.user,
            moderated_at=timezone.now()
        )
    approve_reviews.short_description = "Aprobar reseñas seleccionadas"

    def reject_reviews(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status=Review.Status.REJECTED,
            moderated_by=request.user,
            moderated_at=timezone.now()
        )
    reject_reviews.short_description = "Rechazar reseñas seleccionadas"