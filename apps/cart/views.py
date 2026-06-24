from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST

from apps.products.models import Product
from .utils import (
    get_cart, add_to_cart, update_cart, remove_from_cart,
    get_cart_totals, get_cart_count,
)


def cart_view(request):
    """Display the shopping cart page."""
    cart = get_cart(request)
    totals = get_cart_totals(request)

    # Enrich cart items with product data for display
    cart_items = []
    for item_key, item in cart.items():
        try:
            product = Product.objects.get(pk=item['product_id'])
            cart_items.append({
                **item,
                'product': product,
            })
        except Product.DoesNotExist:
            continue

    context = {
        'cart_items': cart_items,
        'totals': totals,
    }
    return render(request, 'cart/cart.html', context)


def cart_add_view(request, product_id):
    """Add a product to the cart."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1)) if request.method == 'POST' else 1

    add_to_cart(request, product_id, quantity)
    messages.success(request, f'"{product.name}" added to cart.')

    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': get_cart_count(request),
            'message': f'"{product.name}" added to cart.',
        })

    # Otherwise redirect back
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


@require_POST
def cart_update_view(request):
    """Update cart item quantity (AJAX)."""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 0))

    update_cart(request, product_id, quantity)
    totals = get_cart_totals(request)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': get_cart_count(request),
            'totals': {
                'subtotal': str(totals['subtotal']),
                'tax': str(totals['tax']),
                'shipping': str(totals['shipping']),
                'total': str(totals['total']),
            },
        })

    return redirect('cart:cart')


def cart_remove_view(request, product_id):
    """Remove a product from the cart."""
    remove_from_cart(request, product_id)
    messages.info(request, 'Item removed from cart.')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        totals = get_cart_totals(request)
        return JsonResponse({
            'success': True,
            'cart_count': get_cart_count(request),
            'totals': {
                'subtotal': str(totals['subtotal']),
                'tax': str(totals['tax']),
                'shipping': str(totals['shipping']),
                'total': str(totals['total']),
            },
        })

    return redirect('cart:cart')
