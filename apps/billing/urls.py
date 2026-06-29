# apps/billing/urls.py
from django.urls import path
from apps.billing import views

urlpatterns = [
    path("<int:order_id>/",          views.InvoiceDetailView.as_view(),   name="invoice-detail"),
    path("<int:order_id>/download/", views.InvoiceDownloadView.as_view(), name="invoice-download"),
]