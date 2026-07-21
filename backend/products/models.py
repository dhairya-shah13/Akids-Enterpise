from django.db import models
from django.contrib.auth.models import User
from django.db import transaction


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=200, blank=True)
    shipping_address = models.TextField(blank=True)

    def __str__(self):
        return f"Profile: {self.user.username}"


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
    source = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('catalogue', 'Catalogue')], default='admin')
    needs_image = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def display_image(self):
        if self.image_file:
            return self.image_file.url
        elif self.image_url:
            url = self.image_url
            if 'drive.google.com' in url:
                import re
                # Match /file/d/<file_id>/view or similar
                match = re.search(r'/file/d/([^/]+)', url)
                if match:
                    return f"https://lh3.googleusercontent.com/d/{match.group(1)}"
                # Match open?id=<file_id>
                match_id = re.search(r'[?&]id=([^&]+)', url)
                if match_id:
                    return f"https://lh3.googleusercontent.com/d/{match_id.group(1)}"
            return url
        return "https://images.unsplash.com/photo-1545558014-8692077e9b5c?auto=format&fit=crop&w=600&q=80"

    def __str__(self):
        return self.name


class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('CLOSED', 'Closed'),
    ]
    MODULE_CHOICES = [
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
        ('mr_sports', 'MR Sports'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inquiries', null=True, blank=True)
    name = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=254, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    
    module = models.CharField(max_length=20, choices=MODULE_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        prod_name = self.product.name if self.product else f"General Module ({self.module})"
        return f"Inquiry for {prod_name} by {self.name}"


class InquiryLineItem(models.Model):
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='line_items')
    product_code = models.CharField(max_length=100)
    product_name = models.CharField(max_length=255, default='Unknown Product')
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product_name} ({self.product_code}) x {self.quantity} in Inquiry {self.inquiry.id}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('PLACED', 'Placed'),
        ('CONFIRMED', 'Confirmed'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'),
    ]
    
    order_no = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=255)
    shipping_address = models.TextField()
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLACED')
    status_updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_no:
            with transaction.atomic():
                # Lock and fetch last order to generate sequential order_no
                last_order = Order.objects.select_for_update().order_by('id').last()
                if last_order and last_order.order_no:
                    try:
                        last_no = int(last_order.order_no.split('-')[1])
                        new_no = last_no + 1
                    except (ValueError, IndexError):
                        new_no = 1
                else:
                    new_no = 1
                self.order_no = f"ORD-{new_no:05d}"
        super().save(*args, **kwargs)

    def recalculate_total(self):
        self.total_amount = sum(item.subtotal for item in self.items.all())
        self.save(update_fields=['total_amount'])

    def __str__(self):
        return self.order_no


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=255)  # Snapshot
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Update total amount on parent order
        self.order.recalculate_total()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.recalculate_total()

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


STATUS_TRANSITIONS = {
    'PLACED': ['CONFIRMED', 'CANCELLED'],
    'CONFIRMED': ['PACKED', 'CANCELLED'],
    'PACKED': ['SHIPPED', 'CANCELLED'],
    'SHIPPED': ['DELIVERED', 'CANCELLED', 'RETURNED'],
    'DELIVERED': ['RETURNED'],
    'CANCELLED': [],
    'RETURNED': []
}




