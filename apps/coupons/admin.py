# apps/coupons/admin.py
from django.contrib import admin
from apps.coupons.models import Coupon, CouponUsage


class CouponUsageInline(admin.TabularInline):
    model           = CouponUsage
    extra           = 0
    readonly_fields = ["user", "used_at", "order_id"]
    can_delete      = False


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display  = [
        "code", "discount_type", "discount_value",
        "current_uses", "max_uses", "is_active",
        "valid_from", "valid_until"
    ]
    list_filter   = ["discount_type", "is_active"]
    search_fields = ["code", "description"]
    inlines       = [CouponUsageInline]


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display  = ["coupon", "user", "used_at", "order_id"]
    list_filter   = ["coupon"]
    search_fields = ["user__email", "coupon__code"]