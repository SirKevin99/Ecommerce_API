# apps/reviews/views.py
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.reviews.models import Review
from apps.products.models import Product
from apps.reviews.serializers import (
    ReviewSerializer,
    CreateReviewSerializer,
    ModerateReviewSerializer,
    ProductRatingSerializer,
)
from apps.reviews.services import ReviewService


class ProductReviewListView(generics.ListAPIView):
    """GET → lista reseñas aprobadas de un producto."""
    serializer_class   = ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Review.objects.filter(
            product_id=self.kwargs["product_id"],
            status=Review.Status.APPROVED
        ).select_related("user")


class CreateReviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CreateReviewSerializer,
        responses={201: ReviewSerializer},
        summary="Crear reseña",
        description="Solo podés reseñar productos comprados en órdenes entregadas."
    )
    def post(self, request, product_id):
        get_object_or_404(Product, id=product_id, is_active=True)

        serializer = CreateReviewSerializer(
            data={**request.data, "product": product_id},
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()

        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED
        )


class ProductRatingSummaryView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: ProductRatingSerializer},
        summary="Resumen de rating",
        description="Retorna promedio y desglose de estrellas de un producto."
    )
    def get(self, request, product_id):
        get_object_or_404(Product, id=product_id, is_active=True)
        summary = ReviewService.get_product_rating_summary(product_id)
        return Response(summary)


class MyReviewsView(generics.ListAPIView):
    """GET → lista las reseñas del usuario autenticado."""
    serializer_class   = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)


class AdminReviewModerationView(APIView):
    """PATCH → aprobar o rechazar una reseña (solo admin)."""
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=ModerateReviewSerializer,
        responses={200: ReviewSerializer},
        summary="Moderar reseña",
        description="Aprueba o rechaza una reseña. Si rechaza, indicar motivo."
    )
    def patch(self, request, review_id):
        review     = get_object_or_404(Review, id=review_id)
        serializer = ModerateReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = ReviewService.moderate_review(
            review = review,
            action = serializer.validated_data["action"],
            admin  = request.user,
            reason = serializer.validated_data.get("reject_reason", "")
        )
        return Response(ReviewSerializer(review).data)


class AdminPendingReviewsView(generics.ListAPIView):
    """GET → lista reseñas pendientes de moderación (solo admin)."""
    serializer_class   = ReviewSerializer
    permission_classes = [IsAdminUser]
    queryset           = Review.objects.filter(
                           status=Review.Status.PENDING
                         ).select_related("user", "product")