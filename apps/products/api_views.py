from django.http import JsonResponse
from django.db.models import Q
from .models import Product


def search_products(request):
    """API endpoint for live search — returns JSON array of matching products."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)

    products = Product.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query),
        is_active=True
    ).select_related('category')[:8]

    results = []
    for p in products:
        results.append({
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'sku': p.sku,
            'price': str(p.price),
            'price_label': p.price_label,
            'category': p.category.name,
            'category_slug': p.category.parent.slug if p.category.parent else p.category.slug,
        })

    return JsonResponse(results, safe=False)
