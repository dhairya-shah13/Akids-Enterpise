from django.db.models import Q
from .models import Product


def search_products(q, category=None):
    """
    Search products by name, description, or SKU.
    Optionally filter by category.
    Returns a queryset ordered by newest first.
    Optimized with only() to fetch only fields needed for listing display.
    """
    if not q:
        queryset = Product.objects.all().prefetch_related('class_specs', 'dimension_specs')
    else:
        queryset = Product.objects.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(sku__icontains=q)
        ).prefetch_related('class_specs', 'dimension_specs')

    if category:
        queryset = queryset.filter(category=category)

    return queryset.order_by('-created_at')
