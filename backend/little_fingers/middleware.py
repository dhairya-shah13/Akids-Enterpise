import time
import logging

from django.middleware.csrf import get_token

logger = logging.getLogger('request_timing')


class CsrfCookieBootstrapMiddleware:
    """Ensures the `csrftoken` cookie is set on every response.

    The hidden {% csrf_token %} form in base.html only sets the cookie when the
    template is actually rendered. Pages served from the cache (@cache_page on
    company_page / view_all_products) skip that render, so a fresh session
    hitting a cached page would otherwise have no csrftoken cookie and every
    AJAX call that reads getCookie('csrftoken') (chat, catalog inquiry) would
    403. Calling get_token(request) here marks CSRF_COOKIE_NEEDS_UPDATE so
    CsrfViewMiddleware sets the cookie on the outgoing response.

    MUST be listed after django.middleware.csrf.CsrfViewMiddleware in MIDDLEWARE
    so its process_response runs before the cookie is written.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            get_token(request)
        except Exception:
            # Never break a page because the CSRF cookie could not be set.
            # Log it so a broken CSRF configuration is never invisible.
            logger.warning("CsrfCookieBootstrapMiddleware: could not set CSRF token", exc_info=True)
        return response


class SecurityHeadersMiddleware:
    """Adds security response headers to every request.

    Covers the "Missing Headers" audit finding: Content-Security-Policy,
    Permissions-Policy and Referrer-Policy. HSTS / nosniff / frame options are
    handled by Django's SecurityMiddleware via settings (production-gated).

    CSP is deliberately lenient for this codebase:
      - script-src/style-src include 'unsafe-inline' because templates ship
        inline scripts/styles and Tailwind utilities; moving them to external
        files with nonces is a future tightening pass (out of scope).
      - Explicit allow-lists for in-use CDNs: Google Fonts, pdf.js (cdnjs),
        Google Drive image host (lh3.googleusercontent.com), Groq API, Firebase.
    """

    CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https://lh3.googleusercontent.com https://images.unsplash.com https://*.supabase.co https://*.supabase.com; "
        "connect-src 'self' https://api.groq.com https://identitytoolkit.googleapis.com https://*.googleapis.com https://*.supabase.co; "
        "frame-src 'self' https://accounts.google.com; "
        "worker-src 'self' https://cdnjs.cloudflare.com blob:; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    PERMISSIONS_POLICY = (
        "camera=(), microphone=(), geolocation=(), payment=(), "
        "usb=(), interest-cohort=()"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = self.CSP
        response['Permissions-Policy'] = self.PERMISSIONS_POLICY
        return response


class RequestTimingMiddleware:
    """Logs response time for every request. Helps identify slow endpoints."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        # Log slow requests (>500ms) as warnings, everything else at debug
        path = request.path
        status = response.status_code
        if duration_ms > 500:
            logger.warning(f"SLOW {status} {path} took {duration_ms:.1f}ms")
        else:
            logger.debug(f"{status} {path} took {duration_ms:.1f}ms")

        response['X-Response-Time'] = f'{duration_ms:.1f}ms'
        return response
