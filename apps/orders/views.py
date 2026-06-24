import datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from apps.cart.utils import get_cart, get_cart_totals, clear_cart
from apps.products.models import Product
from apps.accounts.models import Address
from apps.accounts.forms import AddressForm
from .models import Order, OrderItem


@login_required
def checkout_view(request):
    """Checkout page with address selection, inline address form, and order summary."""
    cart = get_cart(request)
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart:cart')

    # Re-validate stock at checkout
    stock_errors = []
    for item_key, item in cart.items():
        try:
            product = Product.objects.get(pk=item['product_id'], is_active=True)
            if product.stock < item['quantity']:
                stock_errors.append(
                    f'"{product.name}" — only {product.stock} left in stock '
                    f'(you have {item["quantity"]} in cart).'
                )
        except Product.DoesNotExist:
            stock_errors.append(f'Product "{item["name"]}" is no longer available.')

    if stock_errors:
        for err in stock_errors:
            messages.error(request, err)
        return redirect('cart:cart')

    addresses = request.user.addresses.all()
    totals = get_cart_totals(request)
    address_form = AddressForm()

    if request.method == 'POST':
        # Determine which address to use
        selected_address_id = request.POST.get('address_id')

        if selected_address_id == 'new':
            # Inline new address form
            address_form = AddressForm(request.POST)
            if not address_form.is_valid():
                context = {
                    'cart': cart,
                    'totals': totals,
                    'addresses': addresses,
                    'address_form': address_form,
                }
                return render(request, 'orders/checkout.html', context)

            address = address_form.save(commit=False)
            address.user = request.user
            address.save()
        elif selected_address_id:
            address = get_object_or_404(Address, pk=selected_address_id, user=request.user)
        else:
            messages.error(request, 'Please select or add a shipping address.')
            context = {
                'cart': cart,
                'totals': totals,
                'addresses': addresses,
                'address_form': address_form,
            }
            return render(request, 'orders/checkout.html', context)

        # Snapshot the address
        address_snapshot = {
            'label': address.label,
            'full_name': address.full_name,
            'phone': address.phone,
            'line1': address.line1,
            'line2': address.line2,
            'city': address.city,
            'state': address.state,
            'pincode': address.pincode,
        }

        # Create the order atomically
        with transaction.atomic():
            order = Order(
                user=request.user,
                shipping_address=address_snapshot,
                subtotal=totals['subtotal'],
                tax=totals['tax'],
                shipping_charge=totals['shipping'],
                total=totals['total'],
                status='PENDING',
                payment_status='UNPAID',
            )
            order.save()  # triggers order_number generation

            # Create order items with frozen snapshots
            for item_key, item in cart.items():
                product = Product.objects.select_for_update().get(pk=item['product_id'])

                # Final stock check
                if product.stock < item['quantity']:
                    raise ValueError(
                        f'Insufficient stock for "{product.name}". '
                        f'Available: {product.stock}'
                    )

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name_snapshot=product.name,
                    sku_snapshot=product.sku,
                    price_snapshot=product.price,
                    quantity=item['quantity'],
                    total=Decimal(item['price']) * item['quantity'],
                )

        # Redirect to payment simulation
        return redirect('orders:payment_simulate', order_number=order.order_number)

    context = {
        'cart': cart,
        'totals': totals,
        'addresses': addresses,
        'address_form': address_form,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def payment_simulate_view(request, order_number):
    """Mock payment gateway page."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if order.payment_status != 'UNPAID':
        return redirect('orders:order_confirm', order_number=order.order_number)

    return render(request, 'orders/payment_simulate.html', {'order': order})


@login_required
def payment_process_view(request, order_number):
    """Process the simulated payment (POST only)."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if request.method != 'POST':
        return redirect('orders:payment_simulate', order_number=order_number)

    result = request.POST.get('result', 'failure')

    if result == 'success':
        try:
            order.payment_status = 'SIMULATED'
            order.status = 'CONFIRMED'
            order.warranty_start_date = datetime.date.today()
            order.save()  # triggers stock reduction via signal

            # Clear the cart
            clear_cart(request)
            messages.success(request, f'Payment simulated successfully! Order {order.order_number} confirmed.')
            return redirect('orders:order_confirm', order_number=order.order_number)

        except ValueError as e:
            messages.error(request, str(e))
            order.status = 'CANCELLED'
            order.save()
            return redirect('cart:cart')
    else:
        order.status = 'CANCELLED'
        order.save()
        messages.error(request, 'Payment simulation failed. Order has been cancelled.')
        return redirect('cart:cart')


@login_required
def order_confirm_view(request, order_number):
    """Post-payment order confirmation page."""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        order_number=order_number, user=request.user
    )
    return render(request, 'orders/order_confirm.html', {'order': order})
