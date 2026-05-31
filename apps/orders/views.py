# apps/orders/views.py
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404

from apps.orders.models import Order
from apps.orders.serializers import (
    CreateOrderSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    UpdateOrderStatusSerializer,
)
from apps.orders.services import OrderService


class CreateOrderView(APIView):
    """POST → crea una orden desde el carrito del usuario."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = OrderService.create_order_from_cart(
                user=request.user,
                data=serializer.validated_data
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED
        )


class OrderHistoryView(generics.ListAPIView):
    """GET → historial de órdenes del usuario autenticado."""
    serializer_class   = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related("items").order_by("-created_at")


class OrderDetailView(APIView):
    """GET → detalle completo de una orden del usuario."""
    permission_classes = [IsAuthenticated]

    def get_object(self, order_id, user):
        return get_object_or_404(
            Order.objects.prefetch_related(
                "items__variant",
                "status_history__changed_by"
            ),
            id=order_id,
            user=user  # el usuario solo puede ver sus propias órdenes
        )

    def get(self, request, order_id):
        order = self.get_object(order_id, request.user)
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)


class CancelOrderView(APIView):
    """POST → cancela una orden (solo si está en estado permitido)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if not order.can_be_cancelled:
            return Response(
                {"detail": "Esta orden no puede ser cancelada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = OrderService.update_order_status(
                order      = order,
                new_status = Order.Status.CANCELLED,
                changed_by = request.user,
                note       = "Cancelada por el cliente."
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": "Orden cancelada correctamente."},
            status=status.HTTP_200_OK
        )


class AdminOrderListView(generics.ListAPIView):
    """GET → lista todas las órdenes (solo admin)."""
    serializer_class   = OrderListSerializer
    permission_classes = [IsAdminUser]
    queryset           = Order.objects.all().prefetch_related("items")
    filterset_fields   = ["status", "user"]
    search_fields      = ["user__email", "coupon_code"]
    ordering_fields    = ["created_at", "total"]
    ordering           = ["-created_at"]


class AdminUpdateOrderStatusView(APIView):
    """PATCH → cambia el estado de una orden (solo admin)."""
    permission_classes = [IsAdminUser]

    def patch(self, request, order_id):
        order      = get_object_or_404(Order, id=order_id)
        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = OrderService.update_order_status(
                order      = order,
                new_status = serializer.validated_data["status"],
                changed_by = request.user,
                note       = serializer.validated_data.get("note", "")
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_200_OK
        )