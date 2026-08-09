"""Dependency-free per-IP rate limiting backed by Django's cache.

Defense-in-depth: the cache backend in settings is locmem (per serverless
instance), so these limits are per-instance rather than global. The primary
edge-wide defense is Vercel Firewall rate limiting / challenge rules; this
module is the application-level backstop that works even before firewall rules
apply.

The client IP is taken from the first hop of X-Forwarded-For (set by Vercel)
so requests behind the proxy share the real client IP.
"""

from django.core.cache import cache


def client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def is_rate_limited(request, scope, limit, window):
    """Return True when `scope` for this client IP has exceeded `limit` in `window` seconds.

    Best-effort increment; the TTL window resets on each allowed request.
    """
    ip = client_ip(request)
    key = f"rl:{scope}:{ip}"
    count = cache.get(key) or 0
    if count >= limit:
        return True
    cache.set(key, count + 1, window)
    return False
