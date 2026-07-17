from django.shortcuts import redirect
from django.urls import reverse


class AdminRestrictMiddleware:
    """Redirect admin users to the dashboard when they try to access regular pages."""

    # URL names that admins are allowed to visit
    ADMIN_ALLOWED_NAMES = {
        'admin_dashboard',
        'add_product',
        'delete_product',
        'update_order_status',
        'admin_logout',
        'admin_login',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only intercept if user has an admin session
        if request.session.get('is_admin'):
            url_name = request.resolver_match.url_name if request.resolver_match else None

            # Allow AJAX requests and allowed named URLs
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if not is_ajax and url_name and url_name not in self.ADMIN_ALLOWED_NAMES:
                return redirect('admin_dashboard')

        return self.get_response(request)
