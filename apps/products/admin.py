# apps/products/admin.py
from django.contrib import admin
from apps.products.models import (
    Category, Product, ProductImage,
    Attribute, AttributeValue, ProductVariant
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ["name", "slug", "parent", "is_active"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]
    list_filter   = ["is_active"]


class ProductImageInline(admin.TabularInline):
    model  = ProductImage
    extra  = 1
    fields = ["image", "alt_text", "is_primary", "order"]


class ProductVariantInline(admin.TabularInline):
    model  = ProductVariant
    extra  = 1
    fields = ["sku", "price", "stock", "is_active"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display        = ["name", "category", "brand", "is_active", "created_at"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields       = ["name", "brand"]
    list_filter         = ["is_active", "category"]
    inlines             = [ProductImageInline, ProductVariantInline]


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ["attribute", "value"]
    list_filter  = ["attribute"]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display  = ["sku", "product", "price", "stock", "is_active"]
    search_fields = ["sku", "product__name"]
    list_filter   = ["is_active"]