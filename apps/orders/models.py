import random
import datetime

from django.db import models
from django.conf import settings
from apps.products.models import Product


class Order(models.Model):
    """Customer order with status tracking and payment simulation."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('SIMULATED', 'Simulated'),
        ('PAID', 'Paid'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders'
    )
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    shipping_address = models.JSONField()  # snapshot of address at order time
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID'
    )
    notes = models.TextField(blank=True)
    warranty_start_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"

    def generate_order_number(self):
        """Generate order number: AKD-YYYYMMDD-XXXX"""
        date_str = datetime.date.today().strftime('%Y%m%d')
        random_part = random.randint(1000, 9999)
        return f"AKD-{date_str}-{random_part}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate a unique order number
            for _ in range(10):
                number = self.generate_order_number()
                if not Order.objects.filter(order_number=number).exists():
                    self.order_number = number
                    break
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Individual item within an order, with frozen snapshots."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name_snapshot = models.CharField(max_length=255)
    sku_snapshot = models.CharField(max_length=50)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name_snapshot} x{self.quantity}"
