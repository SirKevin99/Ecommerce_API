# apps/billing/admin.py
from django.contrib import admin
from apps.billing.models import Invoice, CompanyProfile


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display  = ["name", "ruc", "timbrado", "timbrado_valid_until", "invoice_sequence"]
    readonly_fields = ["invoice_sequence", "updated_at"]

    def has_add_permission(self, request):
        # Solo permitir un registro
        return not CompanyProfile.objects.exists()


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display    = [
        "invoice_number", "order", "status",
        "subtotal_iva10", "iva10_amount", "total", "issued_at"
    ]
    list_filter     = ["status"]
    search_fields   = ["invoice_number", "order__id"]
    readonly_fields = [
        "invoice_number", "timbrado", "timbrado_valid_until",
        "subtotal_exento", "subtotal_iva5", "subtotal_iva10",
        "iva5_amount", "iva10_amount", "total",
        "issued_at", "updated_at"
    ]