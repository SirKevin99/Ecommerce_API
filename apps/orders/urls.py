# apps/orders/urls.py
from django.urls import path
from apps.orders import views

urlpatterns = [
    # Cliente
    path("",                              views.OrderHistoryView.as_view(),         name="order-history"),
    path("create/",                       views.CreateOrderView.as_view(),          name="order-create"),
    path("<int:order_id>/",               views.OrderDetailView.as_view(),          name="order-detail"),
    path("<int:order_id>/cancel/",        views.CancelOrderView.as_view(),          name="order-cancel"),

    # Admin
    path("admin/all/",                    views.AdminOrderListView.as_view(),       name="admin-order-list"),
    path("admin/<int:order_id>/status/",  views.AdminUpdateOrderStatusView.as_view(), name="admin-order-status"),
]