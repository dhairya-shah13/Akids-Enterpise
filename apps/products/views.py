import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category


# Mapping from URL slug to parent category name
CATEGORY_MAP = {
    'indoor': {
        'parent_slug': 'indoor',
        'title': 'Indoor Collection',
        'tagline': 'Classroom furniture, soft play, puzzles, and engaging educational toys.',
        'hero_class': 'catalogue-hero-indoor',
        'breadcrumb': 'Catalogues / Indoor & Learning',
    },
    'outdoor': {
        'parent_slug': 'outdoor',
        'title': 'Outdoor Collection',
        'tagline': 'Commercial-grade multiplay stations, climbers, swings, and park equipment.',
        'hero_class': 'catalogue-hero-outdoor',
        'breadcrumb': 'Catalogues / Outdoor Play',
    },
    'parts': {
        'parent_slug': 'parts',
        'title': 'Parts & Components',
        'tagline': 'High-quality replacement parts, accessories, slides, and fabrics.',
        'hero_class': 'catalogue-hero-parts',
        'breadcrumb': 'Catalogues / Parts & Components',
    },
}


def product_list_view(request, category_type):
    """Unified catalogue listing for indoor/outdoor/parts."""
    cat_info = CATEGORY_MAP.get(category_type)
    if not cat_info:
        from django.http import Http404
        raise Http404("Category not found")

    # Get the parent category
    parent_category = Category.objects.filter(slug=cat_info['parent_slug']).first()

    # Get all child categories under this parent
    if parent_category:
        child_categories = Category.objects.filter(parent=parent_category, is_active=True)
        category_ids = list(child_categories.values_list('id', flat=True)) + [parent_category.id]
        products = Product.objects.filter(
            category_id__in=category_ids, is_active=True
        ).select_related('category')
    else:
        products = Product.objects.none()
        child_categories = Category.objects.none()

    # Apply search filter from query string
    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(tags__icontains=search_query)
        )

    # Build JSON data for client-side catalogue.js
    products_list = []
    for p in products:
        products_list.append({
            'id': str(p.id),
            'name': p.name,
            'sku': p.sku,
            'price': float(p.price),
            'priceLabel': p.price_label,
            'category': p.category.name,
            'description': p.description,
            'specs': p.specifications,
            'tags': p.tags if isinstance(p.tags, list) else [],
            'inStock': p.is_in_stock(),
            'badge': p.get_badge_display() if p.badge else None,
            'slug': p.slug,
        })

    context = {
        'category_type': category_type,
        'title': cat_info['title'],
        'tagline': cat_info['tagline'],
        'hero_class': cat_info['hero_class'],
        'breadcrumb': cat_info['breadcrumb'],
        'products_json': json.dumps(products_list),
        'products_count': len(products_list),
        'search_query': search_query,
    }
    return render(request, 'products/listing.html', context)


def product_detail_view(request, slug):
    """Product detail page with specifications and warranty info."""
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images'),
        slug=slug, is_active=True
    )

    # Related products from the same category
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'products/detail.html', context)
