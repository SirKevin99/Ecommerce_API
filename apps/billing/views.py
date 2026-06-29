# apps/billing/views.py
import os
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from apps.orders.models import Order
from apps.billing.models import Invoice
from apps.billing.services import InvoiceService


class InvoiceDownloadView(APIView):
    """
    Descarga la factura PDF de una orden confirmada.
    Solo el dueño de la orden puede descargarla.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: None},
        summary="Descargar factura PDF",
        description="Genera y descarga la factura en formato PDF con IVA paraguayo discriminado."
    )
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if order.status not in [Order.Status.CONFIRMED, Order.Status.DELIVERED]:
            return Response(
                {"detail": "La factura solo está disponible para órdenes confirmadas o entregadas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            invoice = InvoiceService.get_or_create_invoice(order)
        except Exception as e:
            return Response(
                {"detail": f"Error al generar la factura: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if not invoice.pdf_file:
            raise Http404("Factura no encontrada.")

        pdf_path = invoice.pdf_file.path
        if not os.path.exists(pdf_path):
            raise Http404("Archivo de factura no encontrado.")

        response = FileResponse(
            open(pdf_path, "rb"),
            content_type="application/pdf"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{invoice.invoice_number}.pdf"'
        )
        return response


class InvoiceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: None},
        summary="Ver datos de factura",
        description="Retorna los metadatos y montos de IVA de la factura."
    )
    def get(self, request, order_id):
        order   = get_object_or_404(Order, id=order_id, user=request.user)
        invoice = get_object_or_404(Invoice, order=order)

        return Response({
            "invoice_number":      invoice.invoice_number,
            "timbrado":            invoice.timbrado,
            "timbrado_valid_until": invoice.timbrado_valid_until,
            "status":              invoice.status,
            "issued_at":           invoice.issued_at,
            "subtotal_exento":     str(invoice.subtotal_exento),
            "subtotal_iva5":       str(invoice.subtotal_iva5),
            "subtotal_iva10":      str(invoice.subtotal_iva10),
            "iva5_amount":         str(invoice.iva5_amount),
            "iva10_amount":        str(invoice.iva10_amount),
            "total_iva":           str(invoice.total_iva),
            "discount_amount":     str(invoice.discount_amount),
            "total":               str(invoice.total),
        })