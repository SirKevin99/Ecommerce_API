# apps/orders/admin.py
from django.contrib import admin
from apps.orders.models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model           = OrderItem
    extra           = 0
    readonly_fields = ["product_name", "variant_sku", "unit_price", "quantity", "subtotal"]
    can_delete      = False


class OrderStatusHistoryInline(admin.TabularInline):
    model           = OrderStatusHistory
    extra           = 0
    readonly_fields = ["status", "changed_by", "note", "changed_at"]
    can_delete      = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = ["id", "user", "status", "total", "coupon_code", "created_at"]
    list_filter     = ["status"]
    search_fields   = ["user__email", "coupon_code"]
    readonly_fields = ["subtotal", "discount_amount", "total", "created_at", "updated_at"]
    inlines         = [OrderItemInline, OrderStatusHistoryInline]