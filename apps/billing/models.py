# apps/billing/models.py
from django.db import models
from django.core.validators import MinValueValidator
from apps.orders.models import Order


class CompanyProfile(models.Model):
    """
    Datos del emisor de facturas — la empresa.
    Solo debe existir un registro (singleton).
    En producción estos datos deben coincidir exactamente
    con los registrados en la SET de Paraguay.
    """
    name               = models.CharField(max_length=255, verbose_name="Razón Social")
    ruc                = models.CharField(max_length=20,  verbose_name="RUC")
    address            = models.TextField(verbose_name="Dirección")
    city               = models.CharField(max_length=100, verbose_name="Ciudad")
    phone              = models.CharField(max_length=50,  blank=True)
    email              = models.EmailField(blank=True)

    # Datos del timbrado SET
    timbrado           = models.CharField(max_length=20,  verbose_name="N° Timbrado")
    timbrado_valid_from = models.DateField(verbose_name="Vigencia desde")
    timbrado_valid_until = models.DateField(verbose_name="Vigencia hasta")

    # Numeración de facturas — formato paraguayo 001-001-XXXXXXX
    invoice_point      = models.CharField(
                           max_length=3,
                           default="001",
                           verbose_name="Punto de expedición"
                         )
    invoice_establishment = models.CharField(
                              max_length=3,
                              default="001",
                              verbose_name="N° establecimiento"
                            )
    invoice_sequence   = models.PositiveIntegerField(
                           default=1,
                           verbose_name="Secuencia actual"
                         )

    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Perfil de Empresa"
        verbose_name_plural = "Perfil de Empresa"

    def __str__(self):
        return f"{self.name} — RUC: {self.ruc}"

    def get_next_invoice_number(self) -> str:
        """
        Genera y reserva el siguiente número de factura.
        Formato oficial paraguayo: 001-001-0000001
        """
        number = f"{self.invoice_establishment}-{self.invoice_point}-{str(self.invoice_sequence).zfill(7)}"
        self.invoice_sequence += 1
        self.save(update_fields=["invoice_sequence"])
        return number

    def save(self, *args, **kwargs):
        # Singleton — solo puede existir un perfil de empresa
        self.pk = 1
        super().save(*args, **kwargs)


class Invoice(models.Model):
    """
    Factura paraguaya vinculada a una orden.

    El IVA en Paraguay se calcula de la siguiente manera:
    - IVA incluido en el precio: IVA = precio * tasa / (1 + tasa)
    - Ejemplo tasa 10%: IVA = precio * 10 / 110
    - Ejemplo tasa 5%:  IVA = precio * 5  / 105
    """

    class Status(models.TextChoices):
        GENERATED = "generated", "Generada"
        SENT      = "sent",      "Enviada"
        CANCELLED = "cancelled", "Cancelada (Anulada)"

    class VATRate(models.TextChoices):
        RATE_10  = "10",  "IVA 10%"
        RATE_5   = "5",   "IVA 5%"
        EXENTO   = "0",   "Exento"

    order            = models.OneToOneField(
                         Order,
                         on_delete=models.PROTECT,
                         related_name="invoice"
                       )
    invoice_number   = models.CharField(
                         max_length=20,
                         unique=True,
                         verbose_name="N° Factura"
                       )
    timbrado         = models.CharField(
                         max_length=20,
                         verbose_name="N° Timbrado"
                       )
    timbrado_valid_until = models.DateField(
                             verbose_name="Vigencia timbrado"
                           )
    status           = models.CharField(
                         max_length=20,
                         choices=Status.choices,
                         default=Status.GENERATED
                       )

    # Montos base (sin IVA)
    subtotal_exento  = models.DecimalField(
                         max_digits=10, decimal_places=2, default=0,
                         verbose_name="Subtotal Exento"
                       )
    subtotal_iva5    = models.DecimalField(
                         max_digits=10, decimal_places=2, default=0,
                         verbose_name="Subtotal gravado 5%"
                       )
    subtotal_iva10   = models.DecimalField(
                         max_digits=10, decimal_places=2, default=0,
                         verbose_name="Subtotal gravado 10%"
                       )

    # IVA discriminado
    iva5_amount      = models.DecimalField(
                         max_digits=10, decimal_places=2, default=0,
                         verbose_name="IVA 5%"
                       )
    iva10_amount     = models.DecimalField(
                         max_digits=10, decimal_places=2, default=0,
                         verbose_name="IVA 10%"
                       )

    # Totales
    discount_amount  = models.DecimalField(
                         max_digits=10, decimal_places=2, default=0
                       )
    total            = models.DecimalField(
                         max_digits=10, decimal_places=2,
                         verbose_name="Total"
                       )

    pdf_file         = models.FileField(
                         upload_to="invoices/",
                         null=True,
                         blank=True
                       )
    issued_at        = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Factura"
        verbose_name_plural = "Facturas"
        ordering            = ["-issued_at"]

    def __str__(self):
        return f"Factura {self.invoice_number} — Orden #{self.order.id}"

    @property
    def total_iva(self):
        return self.iva5_amount + self.iva10_amount