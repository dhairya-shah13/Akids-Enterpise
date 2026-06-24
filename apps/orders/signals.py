"""
Signal to reduce stock atomically when payment is confirmed.
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import models, transaction

from .models import Order


@receiver(pre_save, sender=Order)
def reduce_stock_on_payment(sender, instance, **kwargs):
    """
    When an order's payment_status transitions to SIMULATED or PAID,
    reduce stock for all order items atomically.
    """
    if not instance.pk:
        return

    try:
        previous = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    payment_confirmed = (
        previous.payment_status not in ('SIMULATED', 'PAID') and
        instance.payment_status in ('SIMULATED', 'PAID')
    )

    if payment_confirmed:
        with transaction.atomic():
            for item in instance.items.select_related('product'):
                product = item.product
                if product.stock < item.quantity:
                    raise ValueError(
                        f"Insufficient stock for {product.name}. "
                        f"Available: {product.stock}, Requested: {item.quantity}"
                    )
                product.stock = models.F('stock') - item.quantity
                product.save(update_fields=['stock'])
