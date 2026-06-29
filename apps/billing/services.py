# apps/billing/services.py
import os
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.utils import timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from apps.billing.models import Invoice, CompanyProfile
from apps.orders.models import Order


# ==============================================================================
# CÁLCULO DE IVA PARAGUAYO
# El IVA en Paraguay está incluido en el precio (IVA incluido).
# Fórmula: IVA = precio_total * tasa / (100 + tasa)
# ==============================================================================

def calculate_iva_included(amount: Decimal, rate: int) -> dict:
    """
    Calcula el IVA incluido en el precio para Paraguay.

    Ejemplo con tasa 10% y monto 110:
    - IVA     = 110 * 10 / 110 = 10
    - Base    = 110 - 10       = 100

    Ejemplo con tasa 5% y monto 105:
    - IVA     = 105 * 5 / 105  = 5
    - Base    = 105 - 5        = 100
    """
    if rate == 0:
        return {"base": amount, "iva": Decimal("0.00")}

    divisor = Decimal(str(100 + rate))
    iva     = (amount * Decimal(str(rate)) / divisor).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
              )
    base    = amount - iva
    return {"base": base, "iva": iva}


class InvoiceService:

    @staticmethod
    def get_company_profile() -> CompanyProfile:
        """
        Obtiene el perfil de empresa o crea uno simulado si no existe.
        En producción este registro debe cargarse manualmente en el admin
        con los datos reales del contribuyente.
        """
        profile, created = CompanyProfile.objects.get_or_create(
            pk=1,
            defaults={
                "name":                  "Mi Empresa S.A.",
                "ruc":                   "80012345-1",
                "address":               "Av. Mcal. López 1234",
                "city":                  "Asunción",
                "phone":                 "021-123456",
                "email":                 "info@miempresa.com.py",
                "timbrado":              "12345678",
                "timbrado_valid_from":   timezone.now().date(),
                "timbrado_valid_until":  timezone.now().date().replace(
                                           year=timezone.now().year + 1
                                         ),
                "invoice_point":         "001",
                "invoice_establishment": "001",
                "invoice_sequence":      1,
            }
        )
        return profile

    @staticmethod
    def get_or_create_invoice(order: Order) -> Invoice:
        """
        Obtiene la factura existente o la crea con cálculo de IVA paraguayo.
        """
        try:
            return Invoice.objects.get(order=order)
        except Invoice.DoesNotExist:
            pass

        company = InvoiceService.get_company_profile()

        # ==============================================================
        # CÁLCULO DE IVA POR ÍTEM
        # Por defecto todos los productos aplican IVA 10%.
        # En producción cada ProductVariant debería tener su tasa configurada.
        # ==============================================================
        subtotal_exento = Decimal("0.00")
        subtotal_iva5   = Decimal("0.00")
        subtotal_iva10  = Decimal("0.00")
        iva5_amount     = Decimal("0.00")
        iva10_amount    = Decimal("0.00")

        for item in order.items.all():
            # Por ahora todos los ítems van a IVA 10%
            # En producción: leer item.variant.vat_rate
            result       = calculate_iva_included(item.subtotal, 10)
            subtotal_iva10 += result["base"]
            iva10_amount   += result["iva"]

        # Aplicar descuento proporcional al IVA si hay cupón
        discount = order.discount_amount
        total    = order.total

        invoice = Invoice.objects.create(
            order                = order,
            invoice_number       = company.get_next_invoice_number(),
            timbrado             = company.timbrado,
            timbrado_valid_until = company.timbrado_valid_until,
            subtotal_exento      = subtotal_exento,
            subtotal_iva5        = subtotal_iva5,
            subtotal_iva10       = subtotal_iva10,
            iva5_amount          = iva5_amount,
            iva10_amount         = iva10_amount,
            discount_amount      = discount,
            total                = total,
        )

        InvoiceService.generate_pdf(invoice, company)
        return invoice

    @staticmethod
    def generate_pdf(invoice: Invoice, company: CompanyProfile) -> None:
        """
        Genera el PDF de la factura con formato legal paraguayo.
        """
        order = invoice.order

        invoices_dir = os.path.join(settings.MEDIA_ROOT, "invoices")
        os.makedirs(invoices_dir, exist_ok=True)

        filename = f"{invoice.invoice_number.replace('-', '_')}.pdf"
        filepath = os.path.join(invoices_dir, filename)

        doc    = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        styles = getSampleStyleSheet()
        story  = []

        # ==============================================================
        # ESTILOS
        # ==============================================================
        COLOR_PRIMARY = colors.HexColor("#003087")  # azul formal

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontSize=16,
            fontName="Helvetica-Bold",
            textColor=COLOR_PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=2,
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER,
            spaceAfter=4,
        )
        label_style = ParagraphStyle(
            "Label",
            parent=styles["Normal"],
            fontSize=8,
            fontName="Helvetica-Bold",
            textColor=COLOR_PRIMARY,
        )
        value_style = ParagraphStyle(
            "Value",
            parent=styles["Normal"],
            fontSize=8,
        )
        small_style = ParagraphStyle(
            "Small",
            parent=styles["Normal"],
            fontSize=7,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )

        # ==============================================================
        # ENCABEZADO — DATOS EMPRESA + NÚMERO DE FACTURA
        # ==============================================================

        # Bloque izquierdo: datos empresa
        empresa_data = [
            [Paragraph(company.name, title_style)],
            [Paragraph(f"RUC: {company.ruc}", subtitle_style)],
            [Paragraph(f"{company.address} — {company.city}", subtitle_style)],
            [Paragraph(f"Tel: {company.phone} | {company.email}", subtitle_style)],
        ]

        # Bloque derecho: número de factura (recuadro legal obligatorio)
        factura_box_data = [
            [Paragraph("FACTURA", ParagraphStyle("FB", parent=styles["Normal"],
                fontSize=13, fontName="Helvetica-Bold",
                textColor=COLOR_PRIMARY, alignment=TA_CENTER))],
            [Paragraph(f"N°  {invoice.invoice_number}",
                ParagraphStyle("FN", parent=styles["Normal"],
                fontSize=11, fontName="Helvetica-Bold",
                alignment=TA_CENTER, textColor=colors.red))],
            [Paragraph(f"Timbrado: {invoice.timbrado}",
                ParagraphStyle("FT", parent=styles["Normal"],
                fontSize=8, alignment=TA_CENTER))],
            [Paragraph(
                f"Vigente hasta: {invoice.timbrado_valid_until.strftime('%d/%m/%Y')}",
                ParagraphStyle("FV", parent=styles["Normal"],
                fontSize=7, alignment=TA_CENTER, textColor=colors.grey))],
        ]

        empresa_table  = Table(empresa_data,  colWidths=[11*cm])
        factura_table  = Table(factura_box_data, colWidths=[6.5*cm])
        factura_table.setStyle(TableStyle([
            ("BOX",        (0, 0), (-1, -1), 1.5, COLOR_PRIMARY),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f4ff")),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        header_table = Table(
            [[empresa_table, factura_table]],
            colWidths=[11*cm, 6.5*cm]
        )
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=1.5,
                                color=COLOR_PRIMARY, spaceAfter=8))

        # ==============================================================
        # DATOS DEL CLIENTE Y FECHA
        # ==============================================================
        fecha_emision = invoice.issued_at.strftime("%d/%m/%Y")
        cliente_data  = [
            [
                Paragraph("Señor(es):", label_style),
                Paragraph(order.user.full_name, value_style),
                Paragraph("Fecha:", label_style),
                Paragraph(fecha_emision, value_style),
            ],
            [
                Paragraph("RUC/CI:", label_style),
                Paragraph("—", value_style),
                Paragraph("Condición:", label_style),
                Paragraph("Contado", value_style),
            ],
            [
                Paragraph("Dirección:", label_style),
                Paragraph(
                    f"{order.shipping_address}, {order.shipping_city}",
                    value_style
                ),
                Paragraph("", label_style),
                Paragraph("", value_style),
            ],
        ]
        cliente_table = Table(
            cliente_data,
            colWidths=[2.5*cm, 7.5*cm, 2.5*cm, 5*cm]
        )
        cliente_table.setStyle(TableStyle([
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW",     (0, -1), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ]))
        story.append(cliente_table)
        story.append(Spacer(1, 0.4*cm))

        # ==============================================================
        # DETALLE DE PRODUCTOS
        # ==============================================================
        items_header = [
            "Cant.", "Descripción", "SKU",
            "Precio Unit.\n(IVA inc.)", "Subtotal\n(IVA inc.)"
        ]
        items_data = [items_header]

        for item in order.items.all():
            items_data.append([
                str(item.quantity),
                item.product_name,
                item.variant_sku,
                f"Gs. {item.unit_price:,.0f}",
                f"Gs. {item.subtotal:,.0f}",
            ])

        items_table = Table(
            items_data,
            colWidths=[1.5*cm, 7*cm, 3*cm, 3*cm, 3*cm]
        )
        items_table.setStyle(TableStyle([
            # Encabezado
            ("BACKGROUND",   (0, 0), (-1, 0), COLOR_PRIMARY),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 8),
            ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
            ("VALIGN",       (0, 0), (-1, 0), "MIDDLE"),
            # Datos
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 1), (-1, -1), 8),
            ("ALIGN",        (0, 1), (0, -1), "CENTER"),
            ("ALIGN",        (3, 1), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f5f7ff")]),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.5*cm))

        # ==============================================================
        # LIQUIDACIÓN DE IVA (obligatoria en Paraguay)
        # Dos columnas: izquierda = liquidación IVA, derecha = totales
        # ==============================================================

        # Columna izquierda — discriminación de IVA
        iva_data = [
            [Paragraph("LIQUIDACIÓN DEL IVA", ParagraphStyle(
                "IVATitle", parent=styles["Normal"],
                fontSize=8, fontName="Helvetica-Bold",
                textColor=COLOR_PRIMARY
            ))],
        ]
        iva_detail = [
            ["Gravado 10%:", f"Gs. {invoice.subtotal_iva10:,.0f}",
             "IVA 10%:", f"Gs. {invoice.iva10_amount:,.0f}"],
            ["Gravado 5%:",  f"Gs. {invoice.subtotal_iva5:,.0f}",
             "IVA 5%:",  f"Gs. {invoice.iva5_amount:,.0f}"],
            ["Exento:",      f"Gs. {invoice.subtotal_exento:,.0f}",
             "", ""],
        ]
        iva_detail_table = Table(iva_detail, colWidths=[2.5*cm, 2.5*cm, 1.8*cm, 2.2*cm])
        iva_detail_table.setStyle(TableStyle([
            ("FONTNAME",  (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",  (0, 0), (-1, -1), 7),
            ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME",  (2, 0), (2, -1), "Helvetica-Bold"),
            ("ALIGN",     (1, 0), (1, -1), "RIGHT"),
            ("ALIGN",     (3, 0), (3, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BOX",       (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#eeeeee")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
        ]))

        # Columna derecha — totales
        totals_data = []
        if invoice.discount_amount > 0:
            totals_data.append(
                ["Subtotal:", f"Gs. {order.subtotal:,.0f}"]
            )
            totals_data.append(
                [f"Descuento ({order.coupon_code}):",
                 f"- Gs. {invoice.discount_amount:,.0f}"]
            )
        totals_data.append(
            ["IVA Total:", f"Gs. {invoice.total_iva:,.0f}"]
        )
        totals_data.append(
            ["TOTAL A PAGAR:", f"Gs. {invoice.total:,.0f}"]
        )

        totals_table = Table(totals_data, colWidths=[4*cm, 3.5*cm])
        totals_table.setStyle(TableStyle([
            ("FONTNAME",   (0, 0), (-1, -2), "Helvetica"),
            ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -2), 8),
            ("FONTSIZE",   (0, -1), (-1, -1), 10),
            ("ALIGN",      (0, 0), (-1, -1), "RIGHT"),
            ("TEXTCOLOR",  (0, -1), (-1, -1), COLOR_PRIMARY),
            ("LINEABOVE",  (0, -1), (-1, -1), 1.5, COLOR_PRIMARY),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOX",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ]))

        bottom_table = Table(
            [[iva_detail_table, totals_table]],
            colWidths=[9*cm, 8.5*cm]
        )
        story.append(bottom_table)
        story.append(Spacer(1, 0.8*cm))

        # ==============================================================
        # PIE DE PÁGINA LEGAL
        # ==============================================================
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.grey, spaceAfter=4))
        story.append(Paragraph(
            "Documento válido como comprobante de pago. "
            "RUC del emisor habilitado por la SET — República del Paraguay.",
            small_style
        ))

        doc.build(story)

        invoice.pdf_file = f"invoices/{filename}"
        invoice.save(update_fields=["pdf_file"])