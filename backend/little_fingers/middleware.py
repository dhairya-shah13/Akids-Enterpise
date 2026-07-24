import time
import logging

logger = logging.getLogger('request_timing')


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
