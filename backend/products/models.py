from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('INDOORS', 'Indoors'),
        ('OUTDOORS', 'Outdoors'),
        ('PARTS', 'Parts'),
        ('MRSPORTS', 'MR Sports'),
    ]
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='INDOORS')
    price = models.DecimalField(max_digits=14, decimal_places=2)
    discount_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    image_file = models.ImageField(upload_to='products/', null=True, blank=True)
    image_url = models.URLField(max_length=1000, null=True, blank=True)
    sku = models.CharField(max_length=50, null=True, blank=True)
    stock = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    # Variant support: parent_product links variant (child) products to a parent product
    # Parent products have parent_product=NULL and are shown in listings.
    # Variant products have parent_product set and are hidden from listings.
    parent_product = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='variants',
        help_text='If set, this product is a variant of the parent product. Variants are hidden from category listings.'
    )

    @property
    def display_image(self):
        if self.image_file:
            return self.image_file.url
        elif self.image_url:
            return self.image_url
        return "https://images.unsplash.com/photo-1545558014-8692077e9b5c?auto=format&fit=crop&w=600&q=80"

    @property
    def is_parent(self):
        """Returns True if this is a parent product (has variants or no parent)."""
        return self.parent_product is None

    @property
    def variant_name(self):
        """Extract the variant-specific part from the product name.
        E.g., 'Rolling Carpet - Size M' → 'Size M'
        """
        if not self.parent_product:
            return None
        parent_name = self.parent_product.name
        child_name = self.name
        if parent_name in child_name:
            suffix = child_name.replace(parent_name, '', 1).strip()
            return suffix.lstrip('-').strip()
        return child_name

    def __str__(self):
        if self.parent_product:
            variant_label = self.variant_name or self.sku or ''
            return f"{self.parent_product.name} ({variant_label})"
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('DISPATCHED', 'Dispatched'),
        ('IN_TRANSIT', 'In Transit'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=200, default='Guest')
    customer_email = models.EmailField(max_length=254, default='guest@example.com')
    customer_phone = models.CharField(max_length=20, blank=True, default='')
    shipping_address = models.TextField(blank=True, default='')
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, default='PENDING', choices=[
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ])
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def get_next_status_code(self):
        """Return the next logical status code in the order workflow."""
        next_map = {
            'PENDING': 'DISPATCHED',
            'DISPATCHED': 'IN_TRANSIT',
            'IN_TRANSIT': 'OUT_FOR_DELIVERY',
            'OUT_FOR_DELIVERY': 'DELIVERED',
        }
        return next_map.get(self.status)

    def get_next_status_display(self):
        """Return the human-readable next status name."""
        code = self.get_next_status_code()
        if code:
            return dict(self.STATUS_CHOICES).get(code, code)
        return None

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='order_items')
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50, blank=True, default='')
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, default='Home', help_text='e.g. Home, School, Office')
    full_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=20, blank=True, default='')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.label}: {self.full_address[:50]}"
