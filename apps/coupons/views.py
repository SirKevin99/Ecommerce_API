# apps/coupons/views.py
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from apps.coupons.models import Coupon
from apps.coupons.serializers import (
    CouponSerializer,
    ApplyCouponSerializer,
    CouponPreviewSerializer,
)
from apps.coupons.services import CouponService


# ==============================================================================
# ADMINISTRACIÓN DE CUPONES (solo admins)
# ==============================================================================

class CouponListCreateView(generics.ListCreateAPIView):
    """
    GET  → lista todos los cupones (admin)
    POST → crea un nuevo cupón (admin)
    """
    queryset           = Coupon.objects.all()
    serializer_class   = CouponSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CouponDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    → detalle de un cupón (admin)
    PATCH  → editar cupón (admin)
    DELETE → desactivar cupón (admin) — soft delete
    """
    queryset           = Coupon.objects.all()
    serializer_class   = CouponSerializer
    permission_classes = [IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        coupon           = self.get_object()
        coupon.is_active = False
        coupon.save()
        return Response(
            {"detail": "Cupón desactivado correctamente."},
            status=status.HTTP_200_OK
        )


# ==============================================================================
# APLICAR CUPÓN (usuarios autenticados)
# ==============================================================================

class ApplyCouponView(APIView):
    """
    POST → valida un cupón y retorna el descuento calculado.
    No confirma la orden — solo hace el preview del descuento.
    La confirmación real ocurre en el endpoint de órdenes.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ApplyCouponSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        coupon       = serializer.validated_data["coupon"]
        order_amount = serializer.validated_data["order_amount"]

        preview = CouponService.apply_coupon(coupon, order_amount)

        response_serializer = CouponPreviewSerializer(preview)
        return Response(response_serializer.data, status=status.HTTP_200_OK)