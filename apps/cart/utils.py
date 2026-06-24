"""
Session-based cart utilities.

Cart structure in session:
    session['cart'] = {
        '<product_id>': {
            'product_id': int,
            'name': str,
            'sku': str,
            'price': str,       # string decimal for JSON safety
            'quantity': int,
            'total': str,
        }
    }
"""

from decimal import Decimal
from apps.products.models import Product

CART_SESSION_KEY = 'cart'


def get_cart(request):
    """Get the cart dict from the session."""
    return request.session.get(CART_SESSION_KEY, {})


def _save_cart(request, cart):
    """Save the cart dict back to the session."""
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def add_to_cart(request, product_id, quantity=1):
    """Add a product to the cart or increase its quantity."""
    cart = get_cart(request)
    product_id_str = str(product_id)

    try:
        product = Product.objects.get(pk=product_id, is_active=True)
    except Product.DoesNotExist:
        return cart

    if product_id_str in cart:
        cart[product_id_str]['quantity'] += quantity
    else:
        cart[product_id_str] = {
            'product_id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': str(product.price),
            'quantity': quantity,
        }

    # Update line total
    price = Decimal(cart[product_id_str]['price'])
    qty = cart[product_id_str]['quantity']
    cart[product_id_str]['total'] = str(price * qty)

    _save_cart(request, cart)
    return cart


def update_cart(request, product_id, quantity):
    """Update quantity for a product in the cart."""
    cart = get_cart(request)
    product_id_str = str(product_id)

    if product_id_str in cart:
        if quantity <= 0:
            del cart[product_id_str]
        else:
            cart[product_id_str]['quantity'] = quantity
            price = Decimal(cart[product_id_str]['price'])
            cart[product_id_str]['total'] = str(price * quantity)

    _save_cart(request, cart)
    return cart


def remove_from_cart(request, product_id):
    """Remove a product from the cart entirely."""
    cart = get_cart(request)
    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]

    _save_cart(request, cart)
    return cart


def clear_cart(request):
    """Empty the cart."""
    request.session[CART_SESSION_KEY] = {}
    request.session.modified = True


def get_cart_totals(request):
    """Calculate subtotal, tax (18% GST), shipping, and grand total."""
    cart = get_cart(request)
    subtotal = Decimal('0.00')

    for item in cart.values():
        subtotal += Decimal(item['price']) * item['quantity']

    tax = (subtotal * Decimal('0.18')).quantize(Decimal('0.01'))

    # Free shipping over ₹5,000, otherwise ₹500
    if subtotal >= Decimal('5000') or subtotal == 0:
        shipping = Decimal('0.00')
    else:
        shipping = Decimal('500.00')

    total = subtotal + tax + shipping

    return {
        'subtotal': subtotal,
        'tax': tax,
        'shipping': shipping,
        'total': total,
    }


def get_cart_count(request):
    """Get total number of items in the cart."""
    cart = get_cart(request)
    return sum(item['quantity'] for item in cart.values())
