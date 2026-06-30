# apps/products/views.py
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.products.models import Category, Product, ProductVariant
from apps.products.serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductWriteSerializer,
    ProductVariantSerializer,
)
from apps.products.services import ProductService
from apps.products.filters import ProductFilter


# ==============================================================================
# CATEGORÍAS
# ==============================================================================

class CategoryListView(generics.ListCreateAPIView):
    queryset         = Category.objects.filter(parent=None, is_active=True)
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]


# ==============================================================================
# PRODUCTOS
# ==============================================================================

class ProductListView(generics.ListAPIView):
    """
    Listado público de productos con filtros, búsqueda y ordenamiento.
    """
    serializer_class   = ProductListSerializer
    permission_classes = [AllowAny]
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = ProductFilter
    search_fields      = ["name", "description", "brand"]
    ordering_fields    = ["created_at", "name"]
    ordering           = ["-created_at"]

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related(
            "category"
        ).prefetch_related(
            "images", "variants"
        )


class ProductCreateView(generics.CreateAPIView):
    serializer_class   = ProductWriteSerializer
    permission_classes = [IsAdminUser]

    def get_serializer_context(self):
        return {"request": self.request}


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.filter(is_active=True)
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductDetailSerializer
        return ProductWriteSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

    def destroy(self, request, *args, **kwargs):
        # Soft delete — nunca borrar productos realmente
        # para preservar historial de órdenes
        product = self.get_object()
        product.is_active = False
        product.save()
        return Response(
            {"detail": "Producto desactivado correctamente."},
            status=status.HTTP_200_OK
        )


# ==============================================================================
# VARIANTES
# ==============================================================================

class ProductVariantListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request, product_id):
        variants = ProductVariant.objects.filter(
            product_id=product_id,
            is_active=True
        ).prefetch_related("attributes")
        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data)

    def post(self, request, product_id):
        serializer = ProductVariantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data    = serializer.validated_data
        variant = ProductService.create_variant(product_id, data)

        return Response(
            ProductVariantSerializer(variant).data,
            status=status.HTTP_201_CREATED
        )