# apps/coupons/urls.py
from django.urls import path
from apps.coupons import views

urlpatterns = [
    # Admin
    path("",          views.CouponListCreateView.as_view(), name="coupon-list-create"),
    path("<int:pk>/", views.CouponDetailView.as_view(),     name="coupon-detail"),

    # Usuario
    path("apply/",    views.ApplyCouponView.as_view(),      name="coupon-apply"),
]