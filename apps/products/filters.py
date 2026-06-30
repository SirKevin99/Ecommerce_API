# apps/products/filters.py
import django_filters
from apps.products.models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(
                  field_name="variants__price",
                  lookup_expr="gte"
                )
    max_price = django_filters.NumberFilter(
                  field_name="variants__price",
                  lookup_expr="lte"
                )
    category  = django_filters.CharFilter(
                  field_name="category__slug",
                  lookup_expr="exact"
                )
    in_stock  = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model  = Product
        fields = ["category", "brand", "is_active"]

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(variants__stock__gt=0).distinct()
        return queryset