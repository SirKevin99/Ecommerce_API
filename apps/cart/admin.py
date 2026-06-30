# apps/cart/admin.py
from django.contrib import admin
from apps.cart.models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model  = CartItem
    extra  = 0
    fields = ["variant", "quantity", "added_at"]
    readonly_fields = ["added_at"]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display  = ["user", "total_items", "subtotal", "updated_at"]
    search_fields = ["user__email", "user__first_name"]
    inlines       = [CartItemInline]