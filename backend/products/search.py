from django.db.models import Q
from .models import Product


def search_products(q, category=None):
    """
    Search products by name, description, or SKU.
    Optionally filter by category.
    Returns a queryset ordered by newest first.
    Optimized with only() to fetch only fields needed for listing display.
    """
    fields = ('id', 'name', 'category', 'price', 'discount_price', 'stock',
              'sku', 'source', 'needs_image', 'image_file', 'image_url', 'created_at')

    if not q:
        queryset = Product.objects.all().only(*fields)
    else:
        queryset = Product.objects.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(sku__icontains=q)
        ).only(*fields)

    if category:
        queryset = queryset.filter(category=category)

    return queryset.order_by('-created_at')
