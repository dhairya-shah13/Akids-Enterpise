"""
Data migration: backfill existing Order records with the GST-exclusive pricing
model (business decision — all prices are GST-exclusive, 18% GST added on top).

For every existing order:
    subtotal_amount = sum of line item subtotals (pre-tax)
    gst_amount      = 18% of subtotal
    total_amount    = subtotal + gst

Uses the same math as products.utils.calculate_gst but inlined here so the
migration is self-contained and deterministic.
"""
from decimal import Decimal, ROUND_HALF_UP
from django.db import migrations

GST_RATE = Decimal("0.18")
CENT = Decimal("0.01")


def backfill_orders(apps, schema_editor):
    Order = apps.get_model("products", "Order")

    corrected = 0
    for order in Order.objects.all().iterator():
        # Recompute from line items (authoritative source for existing orders)
        subtotal = Decimal("0.00")
        for item in order.items.all():
            subtotal += Decimal(str(item.subtotal or 0))

        gst = (subtotal * GST_RATE).quantize(CENT, rounding=ROUND_HALF_UP)
        total = subtotal + gst

        changed = (
            Decimal(str(order.subtotal_amount)) != subtotal
            or Decimal(str(order.gst_amount)) != gst
            or Decimal(str(order.total_amount)) != total
        )
        if changed:
            order.subtotal_amount = subtotal
            order.gst_amount = gst
            order.total_amount = total
            order.save(update_fields=["subtotal_amount", "gst_amount", "total_amount"])
            corrected += 1

    print(f"[backfill_orders] Corrected {corrected} existing order(s) to GST-exclusive pricing.")


def noop(apps, schema_editor):
    """Reverse is a no-op (fields are kept; values stay as computed)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0018_order_gst_amount_order_subtotal_amount"),
    ]

    operations = [
        migrations.RunPython(backfill_orders, noop),
    ]
