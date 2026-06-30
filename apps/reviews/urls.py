# apps/reviews/urls.py
from django.urls import path
from apps.reviews import views

urlpatterns = [
    # Públicos
    path("products/<int:product_id>/",         views.ProductReviewListView.as_view(),    name="product-reviews"),
    path("products/<int:product_id>/rating/",  views.ProductRatingSummaryView.as_view(), name="product-rating"),

    # Usuario autenticado
    path("products/<int:product_id>/create/",  views.CreateReviewView.as_view(),         name="review-create"),
    path("my/",                                views.MyReviewsView.as_view(),            name="my-reviews"),

    # Admin
    path("admin/pending/",                     views.AdminPendingReviewsView.as_view(),  name="admin-pending-reviews"),
    path("admin/<int:review_id>/moderate/",    views.AdminReviewModerationView.as_view(), name="admin-moderate-review"),
]