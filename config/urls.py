# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/products/", include("apps.products.urls")),
    path("api/v1/cart/", include("apps.cart.urls")),
    path("api/v1/coupons/", include("apps.coupons.urls")),

    # Documentación automática
    path("api/schema/",  SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",    SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)