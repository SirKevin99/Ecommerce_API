# apps/cart/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.cart.models import Cart, CartItem
from apps.cart.serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)
from apps.cart.services import CartService


class CartView(APIView):
    """
    GET  → retorna el carrito completo del usuario autenticado
    DELETE → vacía el carrito completo
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = CartService.get_or_create_cart(request.user)
        # prefetch para evitar N+1 queries en ítems y variantes
        cart_qs = Cart.objects.prefetch_related(
            "items__variant__product",
            "items__variant__attributes__attribute",
        ).get(id=cart.id)
        serializer = CartSerializer(cart_qs)
        return Response(serializer.data)

    def delete(self, request):
        CartService.clear_cart(request.user)
        return Response(
            {"detail": "Carrito vaciado correctamente."},
            status=status.HTTP_200_OK
        )


class CartAddItemView(APIView):
    """
    POST → agrega un ítem al carrito o suma cantidad si ya existe.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant  = serializer.validated_data["variant"]
        quantity = serializer.validated_data["quantity"]

        try:
            item = CartService.add_item(request.user, variant, quantity)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"detail": "Ítem agregado al carrito.", "item_id": item.id},
            status=status.HTTP_201_CREATED
        )


class CartItemView(APIView):
    """
    PATCH  → actualiza la cantidad de un ítem
    DELETE → elimina un ítem del carrito
    """
    permission_classes = [IsAuthenticated]

    def get_item(self, request, item_id):
        """
        Helper para obtener el ítem verificando que pertenece
        al carrito del usuario autenticado.
        Evita que un usuario modifique ítems de otro carrito.
        """
        return get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user
        )

    def patch(self, request, item_id):
        item       = self.get_item(request, item_id)
        serializer = UpdateCartItemSerializer(
            instance=item,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        updated_item = CartService.update_item(
            item,
            serializer.validated_data["quantity"]
        )
        return Response(
            {"detail": "Cantidad actualizada.", "quantity": updated_item.quantity},
            status=status.HTTP_200_OK
        )

    def delete(self, request, item_id):
        item = self.get_item(request, item_id)
        CartService.remove_item(item)
        return Response(
            {"detail": "Ítem eliminado del carrito."},
            status=status.HTTP_200_OK
        )