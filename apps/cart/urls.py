# apps/cart/urls.py
from django.urls import path
from apps.cart import views

urlpatterns = [
    path("",              views.CartView.as_view(),        name="cart"),
    path("add/",          views.CartAddItemView.as_view(), name="cart-add-item"),
    path("items/<int:item_id>/", views.CartItemView.as_view(),  name="cart-item"),
]