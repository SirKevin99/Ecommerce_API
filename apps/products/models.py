# apps/products/models.py
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User


# ==============================================================================
# CATEGORÍA
# ==============================================================================

class Category(models.Model):
    """
    Categoría jerárquica — una categoría puede tener una categoría padre.
    Ejemplo: Ropa > Hombre > Camisas
    """
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent      = models.ForeignKey(
                    "self",
                    null=True,
                    blank=True,
                    on_delete=models.SET_NULL,
                    related_name="children"
                  )
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Categoría"
        verbose_name_plural = "Categorías"
        ordering            = ["name"]

    def __str__(self):
        return self.name


# ==============================================================================
# PRODUCTO
# ==============================================================================

class Product(models.Model):
    """
    Producto base — contiene la información general.
    El stock y precio específico viven en ProductVariant,
    porque un mismo producto puede tener distintas tallas/colores
    con precios y stocks diferentes.
    """
    name        = models.CharField(max_length=255)
    slug        = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    category    = models.ForeignKey(
                    Category,
                    on_delete=models.PROTECT,   # no se puede borrar una categoría con productos
                    related_name="products"
                  )
    brand       = models.CharField(max_length=100, blank=True)
    is_active   = models.BooleanField(default=True)
    created_by  = models.ForeignKey(
                    User,
                    on_delete=models.SET_NULL,
                    null=True,
                    related_name="products_created"
                  )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Producto"
        verbose_name_plural = "Productos"
        ordering            = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def min_price(self):
        """Precio mínimo entre todas las variantes activas."""
        variants = self.variants.filter(is_active=True)
        if not variants.exists():
            return None
        return variants.order_by("price").first().price

    @property
    def total_stock(self):
        """Stock total sumando todas las variantes."""
        return sum(v.stock for v in self.variants.filter(is_active=True))

    @property
    def is_in_stock(self):
        return self.total_stock > 0


# ==============================================================================
# IMAGEN DE PRODUCTO
# ==============================================================================

class ProductImage(models.Model):
    """
    Un producto puede tener múltiples imágenes.
    is_primary indica cuál es la imagen principal del listado.
    """
    product    = models.ForeignKey(
                   Product,
                   on_delete=models.CASCADE,
                   related_name="images"
                 )
    image      = models.ImageField(upload_to="products/images/")
    alt_text   = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name        = "Imagen de Producto"
        verbose_name_plural = "Imágenes de Producto"
        ordering            = ["order"]

    def __str__(self):
        return f"Imagen de {self.product.name}"

    def save(self, *args, **kwargs):
        # Si esta imagen se marca como primaria,
        # desmarcar todas las demás del mismo producto
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


# ==============================================================================
# ATRIBUTO (talla, color, material, etc.)
# ==============================================================================

class Attribute(models.Model):
    """
    Define el tipo de atributo: Talla, Color, Material, etc.
    Es genérico para no hardcodear tipos específicos.
    """
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name        = "Atributo"
        verbose_name_plural = "Atributos"

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    """
    Valor concreto de un atributo.
    Ejemplo: Atributo=Talla → Valor=XL
             Atributo=Color → Valor=Rojo
    """
    attribute = models.ForeignKey(
                  Attribute,
                  on_delete=models.CASCADE,
                  related_name="values"
                )
    value     = models.CharField(max_length=100)

    class Meta:
        verbose_name        = "Valor de Atributo"
        verbose_name_plural = "Valores de Atributo"
        unique_together     = ("attribute", "value")

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


# ==============================================================================
# VARIANTE DE PRODUCTO
# ==============================================================================

class ProductVariant(models.Model):
    """
    Cada combinación única de atributos de un producto es una variante.
    Ejemplo: Remera Azul → Variante 1: Talla S / Color Azul
                         → Variante 2: Talla M / Color Azul
                         → Variante 3: Talla S / Color Rojo

    El stock y precio se manejan por variante, no por producto.
    Esto permite tener precios distintos por talla o color.
    """
    product    = models.ForeignKey(
                   Product,
                   on_delete=models.CASCADE,
                   related_name="variants"
                 )
    sku        = models.CharField(max_length=100, unique=True)  # código único de variante
    price      = models.DecimalField(
                   max_digits=10,
                   decimal_places=2,
                   validators=[MinValueValidator(0)]
                 )
    stock      = models.PositiveIntegerField(default=0)
    attributes = models.ManyToManyField(
                   AttributeValue,
                   related_name="variants",
                   blank=True
                 )
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Variante de Producto"
        verbose_name_plural = "Variantes de Producto"

    def __str__(self):
        return f"{self.product.name} — SKU: {self.sku}"

    @property
    def is_in_stock(self):
        return self.stock > 0

    def reduce_stock(self, quantity: int) -> None:
        """
        Reduce el stock de forma segura.
        Lanza ValueError si no hay suficiente stock.
        La lógica de negocio vive aquí, no en la vista ni en el service.
        """
        if quantity <= 0:
            raise ValueError("La cantidad debe ser mayor a cero.")
        if self.stock < quantity:
            raise ValueError(
                f"Stock insuficiente. Disponible: {self.stock}, solicitado: {quantity}."
            )
        self.stock -= quantity
        self.save(update_fields=["stock", "updated_at"])

    def restore_stock(self, quantity: int) -> None:
        """
        Restaura stock cuando se cancela una orden.
        """
        if quantity <= 0:
            raise ValueError("La cantidad debe ser mayor a cero.")
        self.stock += quantity
        self.save(update_fields=["stock", "updated_at"])