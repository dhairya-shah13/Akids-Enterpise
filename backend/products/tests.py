import os
from decimal import Decimal
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from products.models import Product, UserProfile, Address, Order, OrderItem
from little_fingers import settings as project_settings


class ComponentsRemovalTests(TestCase):
    def test_components_route_is_not_available_or_linked_from_home(self):
        self.assertEqual(self.client.get('/parts/').status_code, 404)

        response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'Components')


class CompanyPagesTests(TestCase):
    def test_company_pages_are_available_and_linked_from_footer(self):
        for name in ('about', 'safety_standards', 'testimonials', 'contact', 'privacy_policy', 'terms_of_service'):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('home'))
        self.assertContains(response, reverse('privacy_policy'))
        self.assertContains(response, reverse('contact'))


class ShreemSportsTests(TestCase):
    def test_shreem_sports_page_uses_its_new_name_and_olive_background(self):
        response = self.client.get(reverse('shreemsports'))

        self.assertContains(response, 'Shreem Sports')
        self.assertContains(response, 'background-color: #e7e9cf')


class AdminProductManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('adminuser', 'admin@example.com', 'pass123')

    def test_add_product_with_stock(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('add_product'), {
            'name': 'Test Climbing Arch',
            'category': 'INDOORS',
            'price': '12500',
            'stock': '18',
            'description': 'Safe indoor arch for kids',
            'image_url': ''
        })
        self.assertRedirects(response, reverse('admin_dashboard'))
        product = Product.objects.get(name='Test Climbing Arch')
        self.assertEqual(product.stock, 18)

    def test_edit_product_details(self):
        self.client.force_login(self.admin)
        product = Product.objects.create(name='Old Name', category='INDOORS', price=1000, stock=5, description='Old desc')
        response = self.client.post(reverse('edit_product', args=[product.pk]), {
            'name': 'Updated Name',
            'category': 'OUTDOORS',
            'price': '1500',
            'stock': '25',
            'description': 'Updated desc',
            'image_url': ''
        })
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.name, 'Updated Name')
        self.assertEqual(product.category, 'OUTDOORS')
        self.assertEqual(product.price, 1500)
        self.assertEqual(product.stock, 25)


class UserAddressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')

    def test_address_max_5_cap(self):
        for i in range(5):
            Address.objects.create(user=self.user, street_address=f"Street {i}")
        
        self.assertEqual(Address.objects.filter(user=self.user).count(), 5)

        with self.assertRaises(ValueError):
            Address.objects.create(user=self.user, street_address="Street 6")

    def test_default_address_toggle(self):
        addr1 = Address.objects.create(user=self.user, street_address="Address 1", is_default=True)
        addr2 = Address.objects.create(user=self.user, street_address="Address 2", is_default=True)
        
        addr1.refresh_from_db()
        self.assertFalse(addr1.is_default)
        self.assertTrue(addr2.is_default)


class UsernameCooldownTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('initialname', 'test@example.com', 'pass123')
        self.profile = UserProfile.objects.get_or_create(user=self.user)[0]

    def test_username_change_cooldown(self):
        self.client.force_login(self.user)
        # First username change succeeds
        response = self.client.post(reverse('profile'), {
            'action': 'update_profile',
            'username': 'newname1',
            'phone_number': '9876543210'
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newname1')

        # Immediate second change should fail with error message
        response = self.client.post(reverse('profile'), {
            'action': 'update_profile',
            'username': 'newname2',
            'phone_number': '9876543210'
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newname1')
        self.assertContains(response, 'Username can only be changed once every 30 days')


# ---------------------------------------------------------------------------
# Security & Financial Integrity Remediation Tests (§2.1–§2.7)
# ---------------------------------------------------------------------------

class HardcodedCredentialRemovalTests(TestCase):
    """§2.1 — No hardcoded admin credentials may exist anywhere in source."""

    def test_no_hardcoded_admin_credentials_in_views_source(self):
        from pathlib import Path
        views_path = Path(__file__).resolve().parent / 'views.py'
        source = views_path.read_text(encoding='utf-8')
        self.assertNotIn('admin@gmail.com', source)
        self.assertNotIn('123456', source)

    def test_no_admin_gmail_literal_in_templates(self):
        from pathlib import Path
        templates_dir = Path(__file__).resolve().parent.parent.parent / 'frontend' / 'templates'
        hits = []
        for template in templates_dir.rglob('*.html'):
            if 'admin@gmail.com' in template.read_text(encoding='utf-8'):
                hits.append(str(template))
        self.assertEqual(hits, [], f"admin@gmail.com still present in: {hits}")

    def test_create_admin_from_env_command_creates_superuser(self):
        env_patch = {'ADMIN_EMAIL': 'boss@example.com', 'ADMIN_PASSWORD': 'S3cret!'}
        with mock.patch.dict(os.environ, env_patch):
            call_command('create_admin_from_env', '--noinput')
        user = User.objects.get(email='boss@example.com')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password('S3cret!'))

    def test_create_admin_from_env_missing_vars_raises(self):
        with mock.patch.dict(os.environ, {'ADMIN_EMAIL': '', 'ADMIN_PASSWORD': ''}, clear=False):
            with self.assertRaises(CommandError):
                call_command('create_admin_from_env', '--noinput')

    def test_create_admin_from_env_updates_existing_user(self):
        User.objects.create_user(username='boss@example.com', email='boss@example.com', password='oldpass')
        with mock.patch.dict(os.environ, {'ADMIN_EMAIL': 'boss@example.com', 'ADMIN_PASSWORD': 'newpass'}):
            call_command('create_admin_from_env', '--noinput')
        user = User.objects.get(email='boss@example.com')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password('newpass'))


class ProductionFailFastTests(TestCase):
    """§2.1/§2.5 — Startup fails fast in production when env vars are missing."""

    def test_fails_without_secret_key_in_production(self):
        with mock.patch.dict(os.environ, {
            'SECRET_KEY': '',
            'ADMIN_EMAIL': 'boss@example.com',
            'ADMIN_PASSWORD': 'S3cret!',
        }, clear=False):
            with self.assertRaises(ImproperlyConfigured):
                project_settings.validate_production_env(debug=False)

    def test_fails_without_admin_env_in_production(self):
        with mock.patch.dict(os.environ, {
            'SECRET_KEY': 'x' * 50,
            'ADMIN_EMAIL': '',
            'ADMIN_PASSWORD': '',
        }, clear=False):
            with self.assertRaises(ImproperlyConfigured):
                project_settings.validate_production_env(debug=False)

    def test_passes_with_all_required_vars_in_production(self):
        with mock.patch.dict(os.environ, {
            'SECRET_KEY': 'x' * 50,
            'ADMIN_EMAIL': 'boss@example.com',
            'ADMIN_PASSWORD': 'S3cret!',
        }, clear=False):
            # Should not raise
            project_settings.validate_production_env(debug=False)


class AllowedHostsTests(TestCase):
    """§2.5 — Regression: the ALLOWED_HOSTS allow-list must include the real
    production www hostname. A typo ('www.akidsenterprice.com', missing the
    second 'e') caused a live 400 Bad Request after the apex 308-redirected to
    www, because Django's DisallowedHost check rejected the genuine host."""

    def _effective_allowed_hosts(self):
        # Recompute the allow-list as if no ALLOWED_HOSTS env var is set, so the
        # test is hermetic regardless of a developer/CI shell exporting one.
        with mock.patch.dict(os.environ, {'ALLOWED_HOSTS': ''}, clear=False):
            default = project_settings._DEFAULT_ALLOWED_HOSTS
        return [h.strip() for h in default.split(',') if h.strip()]

    def test_default_allowed_hosts_includes_production_www(self):
        hosts = self._effective_allowed_hosts()
        self.assertIn('akidsenterprise.com', hosts)
        self.assertIn('www.akidsenterprise.com', hosts)

    def test_default_allowed_hosts_has_no_typo(self):
        hosts = self._effective_allowed_hosts()
        self.assertNotIn('akidsenterprice.com', hosts)

    def test_default_allowed_hosts_keeps_dev_and_preview(self):
        hosts = self._effective_allowed_hosts()
        for host in ('localhost', '127.0.0.1', '.vercel.app'):
            self.assertIn(host, hosts)


class SecurityHeadersTests(TestCase):
    """§2.7 — Missing Headers: CSP, Permissions-Policy, Referrer-Policy, nosniff."""

    def test_security_headers_present_on_storefront_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Content-Security-Policy', response)
        self.assertIn('Permissions-Policy', response)
        self.assertIn('Referrer-Policy', response)
        self.assertIn('X-Content-Type-Options', response)
        csp = response['Content-Security-Policy']
        self.assertIn("default-src 'self'", csp)
        self.assertIn("object-src 'none'", csp)
        # 'unsafe-inline' is a documented tradeoff; no 'unsafe-eval' unless needed
        self.assertNotIn('unsafe-eval', csp)

    def test_csp_allows_in_use_cdns(self):
        response = self.client.get(reverse('home'))
        csp = response['Content-Security-Policy']
        self.assertIn('fonts.googleapis.com', csp)
        self.assertIn('api.groq.com', csp)
        self.assertIn('identitytoolkit.googleapis.com', csp)


class CsrfEnforcementTests(TestCase):
    """§2.6 — State-changing admin APIs must require a valid CSRF token."""

    def setUp(self):
        self.admin = User.objects.create_user(username='csrf_admin', email='csrf@example.com', password='pass123', is_staff=True)
        self.user = User.objects.create_user(username='customer2', email='c2@example.com', password='pass123')
        self.product = Product.objects.create(name='CSP Slide', price=Decimal('1000.00'), description='d', stock=5)
        self.order = Order.objects.create(user=self.user, customer_name='John', shipping_address='Addr 1', order_status='PLACED')
        OrderItem.objects.create(order=self.order, product=self.product, product_name='CSP Slide', quantity=1, unit_price=Decimal('1000.00'))

    def test_order_status_update_rejected_without_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin)
        response = csrf_client.post(
            f"/api/admin/orders/{self.order.id}/status/",
            data='{"action": "next"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_order_status_update_accepted_with_valid_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin)
        # Fetch a page to obtain the csrftoken cookie
        csrf_client.get(reverse('admin_dashboard'))
        token = csrf_client.cookies['csrftoken'].value
        response = csrf_client.post(
            f"/api/admin/orders/{self.order.id}/status/",
            data='{"action": "next"}',
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, 'CONFIRMED')

    def test_catalog_inquiry_rejected_without_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse('submit_catalog_inquiry'),
            data='{"name": "A", "phone_number": "9876543210", "email": "a@b.com", "module": "indoor", "line_items": []}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)


class ChatApiCsrfTests(TestCase):
    """§2.6 — Chat API (removed @csrf_exempt) rejects cross-site POSTs."""

    def test_chat_api_rejects_post_without_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(reverse('chat_api'), data='{"message": "hi"}', content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_csrf_cookie_set_even_on_cached_pages(self):
        """The csrftoken cookie must be present on @cache_page'd pages (which
        skip the hidden {% csrf_token %} form render in base.html) so the chat
        fetch — which reads getCookie('csrftoken') — works on a fresh session.
        company_page is decorated with @cache_page(60*30)."""
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('csrftoken', csrf_client.cookies)
        # The cookie value is non-empty.
        self.assertTrue(csrf_client.cookies['csrftoken'].value)
        # A subsequent POST to the CSRF-protected chat API with that token works.
        token = csrf_client.cookies['csrftoken'].value
        with mock.patch.dict(os.environ, {'GROQ_API_KEY': 'dummy-groq-key'}), \
                mock.patch('products.views.requests.post') as mocked_post:
            mocked_post.return_value.status_code = 200
            mocked_post.return_value.json.return_value = {'choices': [{'message': {'content': 'Hi!'}}]}
            response = csrf_client.post(
                reverse('chat_api'),
                data='{"message": "hi"}',
                content_type='application/json',
                HTTP_X_CSRFTOKEN=token,
            )
        self.assertEqual(response.status_code, 200)


class CheckoutGstIntegrationTests(TestCase):
    """§2.4 — Checkout stores GST-exclusive subtotal + GST separately."""

    def test_checkout_creates_order_with_gst_exclusive_fields(self):
        user = User.objects.create_user(username='buyer', email='buyer@example.com', password='pass123')
        product = Product.objects.create(name='Swing', price=Decimal('5000.00'), description='d', stock=10)
        self.client.force_login(user)
        session = self.client.session
        session['cart'] = {str(product.pk): 2}
        session.save()

        response = self.client.post(reverse('checkout'), {'shipping_address': 'Test Rd 1'})
        self.assertEqual(response.status_code, 302)
        order = Order.objects.latest('id')
        # 2 x 5000 = 10000 pre-tax; 18% GST on top
        self.assertEqual(order.subtotal_amount, Decimal('10000.00'))
        self.assertEqual(order.gst_amount, Decimal('1800.00'))
        self.assertEqual(order.total_amount, Decimal('11800.00'))
        self.assertEqual(order.total_amount, order.subtotal_amount * Decimal('1.18'))

    def test_checkout_tax_breakdown_matches_calculate_gst(self):
        from products.utils import calculate_gst
        tax = calculate_gst(Decimal('1000.00'))
        self.assertEqual(tax['total'], Decimal('1180.00'))
        self.assertEqual(tax['cgst'], Decimal('90.00'))
        self.assertEqual(tax['sgst'], Decimal('90.00'))

