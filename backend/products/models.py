from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('INDOORS', 'Indoors'),
        ('OUTDOORS', 'Outdoors'),
        ('PARTS', 'Parts'),
        ('RFSPORTS', 'RF Sports'),
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
            return self.image_url
        return "https://images.unsplash.com/photo-1545558014-8692077e9b5c?auto=format&fit=crop&w=600&q=80"

    def __str__(self):
        return self.name


class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('CLOSED', 'Closed'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inquiries')
    name = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inquiry for {self.product.name} by {self.name}"

