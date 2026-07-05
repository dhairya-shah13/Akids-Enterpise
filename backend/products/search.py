from django.db.models import Q
from .models import Product

def search_products(q, category=None):
    """
    Search products by name, description, or SKU.
    Optionally filter by category.
    Returns a queryset ordered by newest first.
    """
    if not q:
        queryset = Product.objects.filter(parent_product__isnull=True)
    else:
        queryset = Product.objects.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(sku__icontains=q),
            parent_product__isnull=True
        )
        
    if category:
        queryset = queryset.filter(category=category)
        
    return queryset.order_by('-created_at')
