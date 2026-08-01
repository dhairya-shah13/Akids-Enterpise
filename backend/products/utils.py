"""
Shared financial utilities — single source of truth for all tax math.

BUSINESS DECISION (final): All product prices in the system are **GST-exclusive**.
GST (18%) must always be calculated and added on top at checkout. Everywhere tax
is computed (checkout, order storage, PDF invoice generation, admin reports)
must call :func:`calculate_gst` — never re-implement the math inline.
"""
from decimal import Decimal, ROUND_HALF_UP

GST_RATE = Decimal("0.18")
CGST_RATE = Decimal("0.09")
SGST_RATE = Decimal("0.09")
CENT = Decimal("0.01")


def calculate_gst(subtotal):
    """
    Given a GST-exclusive subtotal, return the GST breakout.

    Returns a dict with:
        subtotal : pre-tax amount (GST-exclusive base)
        gst      : total GST (18% of subtotal)
        cgst     : 9% GST component (rounded half-up)
        sgst     : 9% GST component (gst - cgst, so cgst + sgst == gst exactly)
        total    : subtotal + gst  (the final payable amount)

    :param subtotal: Decimal, int, float or numeric str of the pre-tax total.
    """
    subtotal = Decimal(str(subtotal)).quantize(CENT, rounding=ROUND_HALF_UP)
    gst = (subtotal * GST_RATE).quantize(CENT, rounding=ROUND_HALF_UP)
    cgst = (gst * CGST_RATE / GST_RATE).quantize(CENT, rounding=ROUND_HALF_UP)
    sgst = gst - cgst  # guarantees cgst + sgst == gst
    total = subtotal + gst
    return {
        "subtotal": subtotal,
        "gst": gst,
        "cgst": cgst,
        "sgst": sgst,
        "total": total,
    }
