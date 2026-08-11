"""Dependency-free per-IP rate limiting backed by Django's cache.

Defense-in-depth: the cache backend in settings is locmem (per serverless
instance), so these limits are per-instance rather than global. The primary
edge-wide defense is Cloudflare rate limiting + Vercel Firewall; this module
is the application-level backstop.

Client IP resolution (IMPLEMENTATIONPLAN.md §7):
- `CF-Connecting-IP` is preferred when present. Cloudflare overwrites any
  client-supplied value of this header, so it is authoritative for proxied
  traffic.
- Fall back to the first hop of X-Forwarded-For (Vercel's format) for
  direct-origin traffic. Note Cloudflare APPENDS to X-Forwarded-For rather
  than overwriting it, so the first hop is client-spoofable when a request
  does not carry CF-Connecting-IP.
"""

from django.core.cache import cache


def client_ip(request):
    # Trust model: CF-Connecting-IP is only authoritative because traffic is
    # assumed to arrive via Cloudflare, which overwrites any client-supplied
    # value. It is NOT a hard guarantee on direct-origin traffic (e.g. the
    # vercel.app domain, reachable on Vercel Hobby) where a client can send a
    # fake header — acceptable, since Cloudflare's own rate limiting keys on
    # its view of the IP regardless. Fall back to the first X-Forwarded-For
    # hop (Vercel's format) for direct-origin traffic.
    cf = request.META.get('HTTP_CF_CONNECTING_IP', '').strip()
    if cf:
        return cf
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
