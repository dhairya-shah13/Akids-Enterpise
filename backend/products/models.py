from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db import transaction
from .utils import calculate_gst


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=200, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    shipping_address = models.TextField(blank=True)
    avatar_color = models.CharField(max_length=20, default='sea')
    username_changed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Profile: {self.user.username}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=200, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    street_address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def save(self, *args, **kwargs):
        if not self.pk and Address.objects.filter(user=self.user).count() >= 5:
            raise ValueError("Maximum 5 saved addresses allowed per account.")
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.street_address[:30]} ({'Default' if self.is_default else 'Saved'})"


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('INDOORS', 'Indoors'),
        ('OUTDOORS', 'Outdoors'),
        ('PARTS', 'Parts'),
        ('SHREEM_SPORTS', 'Shreem Sports'),
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
    colours = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['category'], name='product_category_idx'),
            models.Index(fields=['sku'], name='product_sku_idx'),
            models.Index(fields=['-created_at'], name='product_created_idx'),
        ]

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
                    return f"https://lh3.googleusercontent.com/d/{match.group(1)}=w400"
                # Match open?id=<file_id>
                match_id = re.search(r'[?&]id=([^&]+)', url)
                if match_id:
                    return f"https://lh3.googleusercontent.com/d/{match_id.group(1)}=w400"
            return url
        return "https://images.unsplash.com/photo-1545558014-8692077e9b5c?auto=format&fit=crop&w=600&q=80"

    def __str__(self):
        return self.name

    @property
    def colours_json(self):
        import json
        return json.dumps(self.colours or [])

    @property
    def colours_with_hex(self):
        from .constants import PRODUCT_COLOURS
        color_map = dict(PRODUCT_COLOURS)
        return [(c, color_map.get(c, '#CCCCCC')) for c in (self.colours or [])]

    def get_class_specs_json(self):
        import json
        specs = self.class_specs.all().order_by('order')
        data = []
        for s in specs:
            data.append({
                'id': s.id,
                'class_label': s.class_label,
                'age_min': s.age_min,
                'age_max': s.age_max,
            })
        return json.dumps(data)

    def get_dimension_specs_json(self):
        import json
        specs = self.dimension_specs.all().order_by('order')
        data = []
        for s in specs:
            data.append({
                'id': s.id,
                'group_label': s.group_label,
                'component': s.component,
                'length': s.length,
                'width': s.width,
                'height': s.height,
                'unit': s.unit,
                'notes': s.notes,
            })
        return json.dumps(data)


class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('CLOSED', 'Closed'),
    ]
    MODULE_CHOICES = [
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
        ('shreem_sports', 'Shreem Sports'),
    ]
    CLOSURE_OUTCOME_CHOICES = [
        ('WON', 'Customer Won'),
        ('LOST', 'Customer Lost'),
    ]
    inquiry_no = models.CharField(max_length=20, unique=True, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inquiries', null=True, blank=True)
    name = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=254, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    
    module = models.CharField(max_length=20, choices=MODULE_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    closure_outcome = models.CharField(max_length=10, choices=CLOSURE_OUTCOME_CHOICES, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.inquiry_no:
            with transaction.atomic():
                last_inquiry = Inquiry.objects.select_for_update().order_by('id').last()
                if last_inquiry and last_inquiry.inquiry_no:
                    try:
                        last_no = int(last_inquiry.inquiry_no.split('-')[1])
                        new_no = last_no + 1
                    except (ValueError, IndexError):
                        new_no = 1
                else:
                    new_no = 1
                self.inquiry_no = f"INQ-{new_no:04d}"
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['status'], name='inquiry_status_idx'),
            models.Index(fields=['module'], name='inquiry_module_idx'),
            models.Index(fields=['-created_at'], name='inquiry_created_idx'),
        ]

    def __str__(self):
        prod_name = self.product.name if self.product else f"General Module ({self.module})"
        return f"{self.inquiry_no} - Inquiry for {prod_name} by {self.name}"


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
    # Financial fields: subtotal is GST-exclusive, gst_amount is the 18% GST
    # computed on top, total_amount is the final payable (subtotal + GST).
    subtotal_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    gst_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_status'], name='order_status_idx'),
            models.Index(fields=['-created_at'], name='order_created_idx'),
        ]

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
        """
        Recompute financial fields from line items using the GST-exclusive
        pricing model (single source of truth: products.utils.calculate_gst).
        subtotal_amount = sum of item subtotals (pre-tax)
        gst_amount      = 18% GST added on top
        total_amount    = subtotal + GST (final payable)
        """
        from django.db.models import Sum
        result = self.items.aggregate(total=Sum('subtotal'))
        subtotal = result['total'] or Decimal('0.00')
        calc = calculate_gst(subtotal)
        self.subtotal_amount = calc['subtotal']
        self.gst_amount = calc['gst']
        self.total_amount = calc['total']
        self.save(update_fields=['subtotal_amount', 'gst_amount', 'total_amount'])

    def __str__(self):
        return self.order_no


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=255)  # Snapshot
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    colour = models.CharField(max_length=50, blank=True, null=True)
    dimension = models.CharField(max_length=100, blank=True, null=True)

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


class ProductClassSpec(models.Model):
    product = models.ForeignKey(Product, related_name="class_specs", on_delete=models.CASCADE)
    class_label = models.CharField(max_length=50)
    age_min = models.PositiveIntegerField()
    age_max = models.PositiveIntegerField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.class_label}"


class ProductDimensionSpec(models.Model):
    product = models.ForeignKey(Product, related_name="dimension_specs", on_delete=models.CASCADE)
    group_label = models.CharField(max_length=50, blank=True, default="")
    component = models.CharField(max_length=100, blank=True, default="")
    length = models.CharField(max_length=50)
    width = models.CharField(max_length=50, blank=True, default="")
    height = models.CharField(max_length=50, blank=True, default="")
    unit = models.CharField(max_length=10, choices=[("cm", "cm"), ("inch", "inch"), ("mm", "mm"), ("ft", "ft")], default="cm")
    notes = models.CharField(max_length=100, blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        comp_str = f"[{self.component}] " if self.component else ""
        height_str = f" x {self.height}" if self.height else ""
        width_str = f" x {self.width}" if self.width else ""
        group_str = f" ({self.group_label})" if self.group_label else ""
        notes_str = f" ({self.notes})" if self.notes else ""
        return f"{self.product.name} - {comp_str}{self.length}{width_str}{height_str} {self.unit}{group_str}{notes_str}"


STATUS_TRANSITIONS = {
    'PLACED': ['CONFIRMED', 'CANCELLED'],
    'CONFIRMED': ['PACKED', 'CANCELLED'],
    'PACKED': ['SHIPPED', 'CANCELLED'],
    'SHIPPED': ['DELIVERED', 'CANCELLED', 'RETURNED'],
    'DELIVERED': ['RETURNED'],
    'CANCELLED': [],
    'RETURNED': []
}




