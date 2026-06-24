"""
Context processor to make cart_count available in all templates.
Registered in config/settings.py TEMPLATES context_processors.
"""

from .utils import get_cart_count


def cart_context(request):
    return {
        'cart_count': get_cart_count(request),
    }
