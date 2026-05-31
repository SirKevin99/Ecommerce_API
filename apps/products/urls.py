# apps/products/urls.py
from django.urls import path
from apps.products import views

urlpatterns = [
    # Categorías
    path("categories/",                    views.CategoryListView.as_view(),           name="category-list"),

    # Productos
    path("",                               views.ProductListView.as_view(),            name="product-list"),
    path("create/",                        views.ProductCreateView.as_view(),          name="product-create"),
    path("<slug:slug>/",                   views.ProductDetailView.as_view(),          name="product-detail"),

    # Variantes
    path("<int:product_id>/variants/",     views.ProductVariantListCreateView.as_view(), name="variant-list-create"),
]