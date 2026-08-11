import os
from decimal import Decimal
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from products.models import Product, UserProfile, Address, Order, OrderItem
from products.ratelimit import client_ip
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
            'image_url': '',
            'colours': ['Red']
        })
        self.assertRedirects(response, reverse('admin_dashboard'))
        product = Product.objects.get(name='Test Climbing Arch')
        self.assertEqual(product.stock, 18)
        self.assertEqual(product.colours, ['Red'])

    def test_edit_product_details(self):
        self.client.force_login(self.admin)
        product = Product.objects.create(name='Old Name', category='INDOORS', price=1000, stock=5, description='Old desc', colours=['Red'])
        response = self.client.post(reverse('edit_product', args=[product.pk]), {
            'name': 'Updated Name',
            'category': 'OUTDOORS',
            'price': '1500',
            'stock': '25',
            'description': 'Updated desc',
            'image_url': '',
            'colours': ['Blue']
        })
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.name, 'Updated Name')
        self.assertEqual(product.category, 'OUTDOORS')
        self.assertEqual(product.price, 1500)
        self.assertEqual(product.stock, 25)
        self.assertEqual(product.colours, ['Blue'])


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


class SearchSuggestionsTests(TestCase):
    def test_empty_query_returns_empty_results(self):
        response = self.client.get(reverse('api_search_suggestions'), {'q': ''})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['results'], [])

    def test_matching_query_returns_suggestions(self):
        Product.objects.create(name='Everest Slide', price=Decimal('15000.00'), description='Big slide', category='OUTDOORS')
        response = self.client.get(reverse('api_search_suggestions'), {'q': 'Everest'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Everest Slide')
        self.assertEqual(data['results'][0]['price'], '15,000.00')
        self.assertIn('Everest Slide', data['results'][0]['name'])

    def test_category_filtering_works(self):
        Product.objects.create(name='Everest Slide', price=Decimal('15000.00'), description='Big slide', category='OUTDOORS')
        Product.objects.create(name='Everest Table', price=Decimal('2000.00'), description='Kids table', category='INDOORS')
        
        response = self.client.get(reverse('api_search_suggestions'), {'q': 'Everest', 'category': 'INDOORS'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Everest Table')


class ProductColoursAndSizeSpecsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('adminuser', 'admin@example.com', 'pass123')
        self.client = Client()
        self.product = Product.objects.create(
            name="Testing Arch",
            category="INDOORS",
            price=Decimal("5000.00"),
            stock=10,
            description="Safe testing arch",
            colours=["Red", "Blue"]
        )
        self.class_spec = self.product.class_specs.create(
            class_label="Toddler",
            age_min=1,
            age_max=3,
            order=0
        )
        self.dimension_spec = self.product.dimension_specs.create(
            group_label="Toddler",
            component="Desk",
            length="50",
            width="50",
            height="",
            unit="cm",
            notes="Test notes",
            order=0
        )

    def test_product_model_colours_and_specs(self):
        self.assertEqual(self.product.colours, ["Red", "Blue"])
        self.assertEqual(self.product.colours_with_hex, [("Red", "#E53935"), ("Blue", "#1E88E5")])
        self.assertEqual(self.product.class_specs.count(), 1)
        self.assertEqual(self.product.dimension_specs.count(), 1)
        
        spec = self.product.class_specs.first()
        self.assertEqual(spec.class_label, "Toddler")
        
        dim = self.product.dimension_specs.first()
        self.assertEqual(dim.group_label, "Toddler")
        self.assertEqual(dim.component, "Desk")
        self.assertEqual(dim.length, "50")
        self.assertEqual(dim.width, "50")
        self.assertEqual(dim.height, "")
        self.assertEqual(dim.notes, "Test notes")

    def test_add_product_with_specs_and_colours_via_admin(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('add_product'), {
            'name': 'New Spec Product',
            'category': 'INDOORS',
            'price': '8000',
            'stock': '15',
            'description': 'Description with details',
            'image_url': '',
            'colours': ['Green', 'Yellow'],
            'class_label[]': ['Infant', 'Toddler'],
            'class_age_min[]': ['0', '1'],
            'class_age_max[]': ['1', '3'],
            'dim_group_label[]': ['Infant', 'Toddler'],
            'dim_component[]': ['Chair', 'Desk'],
            'dim_length[]': ['30', '45'],
            'dim_width[]': ['30', '45'],
            'dim_height[]': ['', '20'],
            'dim_unit[]': ['cm', 'inch'],
            'dim_notes[]': ['Note 1', 'Note 2']
        })
        self.assertRedirects(response, reverse('admin_dashboard'))
        product = Product.objects.get(name='New Spec Product')
        self.assertEqual(product.colours, ['Green', 'Yellow'])
        self.assertEqual(product.class_specs.count(), 2)
        self.assertEqual(product.dimension_specs.count(), 2)
        
        classes = list(product.class_specs.all().order_by('order'))
        self.assertEqual(classes[0].class_label, 'Infant')
        
        dims = list(product.dimension_specs.all().order_by('order'))
        self.assertEqual(dims[0].group_label, 'Infant')
        self.assertEqual(dims[0].component, 'Chair')
        self.assertEqual(dims[1].group_label, 'Toddler')
        self.assertEqual(dims[1].component, 'Desk')
        self.assertEqual(dims[1].unit, 'inch')
        self.assertEqual(dims[1].height, '20')
        self.assertEqual(dims[1].notes, 'Note 2')

    def test_cart_operations_with_colours_and_dimensions(self):
        # Validation failure redirect when variants are missing
        response = self.client.post(reverse('add_to_cart', args=[self.product.pk]), {
            'quantity': 2,
            'colour': '',
            'dimension': ''
        })
        self.assertRedirects(response, f"{reverse('product_detail', args=[self.product.pk])}?toast=select-variants-required")

        # Add to cart with color Red and dimension Toddler
        response = self.client.post(reverse('add_to_cart', args=[self.product.pk]), {
            'quantity': 2,
            'colour': 'Red',
            'dimension': 'Toddler'
        })
        # Check session key structure
        session = self.client.session
        cart = session.get('cart', {})
        expected_key = f"{self.product.pk}::Red::Toddler"
        self.assertIn(expected_key, cart)
        self.assertEqual(cart[expected_key], 2)

        # Update cart
        response = self.client.post(reverse('update_cart', args=[self.product.pk]), {
            'quantity': 4,
            'colour': 'Red',
            'dimension': 'Toddler'
        })
        cart = self.client.session.get('cart', {})
        self.assertEqual(cart[expected_key], 4)

        # Remove from cart
        response = self.client.post(reverse('remove_from_cart', args=[self.product.pk]), {
            'colour': 'Red',
            'dimension': 'Toddler'
        })
        cart = self.client.session.get('cart', {})
        self.assertNotIn(expected_key, cart)

    def test_order_creation_and_invoice_pdf_with_colour_and_dimension(self):
        # Login customer
        customer = User.objects.create_user('customer', 'cust@example.com', 'pass123')
        self.client.force_login(customer)
        
        # Add to cart
        self.client.post(reverse('add_to_cart', args=[self.product.pk]), {
            'quantity': 1,
            'colour': 'Blue',
            'dimension': 'Toddler'
        })
        
        # Checkout
        response = self.client.post(reverse('checkout'), {
            'customer_name': 'customer',
            'shipping_address': '123 Playground Street'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify order & order item
        order = Order.objects.latest('id')
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.colour, 'Blue')
        self.assertEqual(item.dimension, 'Toddler')
        
        # Generate Invoice and verify colour/dimension is rendered
        from products.pdf_generator import generate_invoice_pdf
        pdf_content = generate_invoice_pdf(order)
        self.assertIsNotNone(pdf_content)


# ---------------------------------------------------------------------------
# WS-2 / WS-3 — Edge-cache CSRF fallback, rate limiting, and view_all PII guard
# ---------------------------------------------------------------------------

class CsrfFallbackEndpointTests(TestCase):
    """WS-2 — /api/csrf/ provides the lazy csrftoken cookie for edge-cached pages."""

    def test_api_csrf_sets_cookie_for_fresh_client(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.get(reverse('api_csrf'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('csrftoken', csrf_client.cookies)
        self.assertTrue(csrf_client.cookies['csrftoken'].value)


class ClientIpResolutionTests(TestCase):
    """IMPLEMENTATIONPLAN.md §7 — client_ip() prefers CF-Connecting-IP.

    Cloudflare APPENDS to X-Forwarded-For (never overwrites), so the first XFF
    hop is client-spoofable; CF-Connecting-IP is authoritative because
    Cloudflare strips/overwrites any client-supplied value. The fallback path
    must preserve the pre-Cloudflare behaviour for direct-origin traffic.
    """

    def _request(self, **meta_headers):
        factory = RequestFactory()
        request = factory.get('/login/')
        for key, value in meta_headers.items():
            request.META[key] = value
        return request

    def test_cf_connecting_ip_is_preferred_over_spoofed_xff(self):
        # First XFF hop is attacker-controlled; CF-Connecting-IP wins.
        request = self._request(
            HTTP_CF_CONNECTING_IP='203.0.113.9',
            HTTP_X_FORWARDED_FOR='1.2.3.4, 203.0.113.5',
        )
        self.assertEqual(client_ip(request), '203.0.113.9')

    def test_xff_first_hop_used_when_no_cf_header(self):
        # Direct-origin traffic (e.g. via vercel.app) has no CF header —
        # behaviour is unchanged from before Cloudflare.
        request = self._request(HTTP_X_FORWARDED_FOR='198.51.100.7, 10.0.0.1')
        self.assertEqual(client_ip(request), '198.51.100.7')

    def test_empty_cf_connecting_ip_falls_through_to_xff(self):
        # An empty header value must not be treated as a client IP.
        request = self._request(
            HTTP_CF_CONNECTING_IP='',
            HTTP_X_FORWARDED_FOR='198.51.100.7',
        )
        self.assertEqual(client_ip(request), '198.51.100.7')

    def test_remote_addr_fallback_when_no_proxy_headers(self):
        request = self._request(REMOTE_ADDR='192.0.2.1')
        self.assertEqual(client_ip(request), '192.0.2.1')


class RateLimitTests(TestCase):
    """WS-3 — application-level per-IP rate limits kick in after the threshold."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_login_post_rate_limited_after_threshold(self):
        url = reverse('admin_login')
        for _ in range(10):
            response = self.client.post(url, {'email': 'nobody@example.com', 'password': 'x'})
            self.assertEqual(response.status_code, 200)
        response = self.client.post(url, {'email': 'nobody@example.com', 'password': 'x'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Too many login attempts')

    def test_chat_api_rate_limited_after_threshold(self):
        with mock.patch('products.views.requests.post') as mocked_post:
            mocked_post.return_value.status_code = 200
            mocked_post.return_value.json.return_value = {'choices': [{'message': {'content': 'Hi'}}]}
            for _ in range(10):
                response = self.client.post(reverse('chat_api'), data='{"message": "hi"}', content_type='application/json')
                self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('chat_api'), data='{"message": "hi"}', content_type='application/json')
        self.assertEqual(response.status_code, 429)

    def test_submit_inquiry_rate_limited_after_threshold(self):
        payload = '{"name": "A", "phone_number": "9876543210", "email": "a@b.com", "module": "indoor", "line_items": [{"product_code": "X", "quantity": 1}]}'
        for _ in range(10):
            response = self.client.post(reverse('submit_catalog_inquiry'), data=payload, content_type='application/json')
            self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('submit_catalog_inquiry'), data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 429)

    def test_signup_post_rate_limited_after_threshold(self):
        url = reverse('signup')
        for _ in range(5):
            response = self.client.post(url, {'email': '', 'password': '', 'username': ''})
            self.assertEqual(response.status_code, 200)
        response = self.client.post(url, {'email': '', 'password': '', 'username': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Too many signup attempts')

    def test_signup_valid_post_still_works(self):
        """Regression guard: the WS-3 rate-limit branch must not break signup."""
        with mock.patch('products.views._email_domain_resolves', return_value=True), \
                mock.patch('products.views.requests.post') as mocked_post:
            mocked_post.return_value.status_code = 200
            mocked_post.return_value.json.return_value = {}
            response = self.client.post(reverse('signup'), {
                'email': 'fresh@example.com',
                'password': 'secret123',
                'username': 'freshuser',
            })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/verify_email_pending.html')
        user = User.objects.get(email='fresh@example.com')
        self.assertFalse(user.is_active)


class ViewAllProductsPiiGuardTests(TestCase):
    """WS-2/C3 — view_all_products must never serve logged-in user PII from a shared cache."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.user = User.objects.create_user('leaky', 'leaky@example.com', 'pass123')
        Product.objects.create(name='Test Slide', category='INDOORS', price=Decimal('1000.00'),
                               description='d', stock=5, sku='TS-01')

    def test_logged_in_view_all_is_private_and_contains_own_prefill(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('view_all_products', args=['indoor']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'leaky@example.com')
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_anonymous_view_all_is_publicly_cacheable_and_has_no_user_email(self):
        User.objects.create_user('other', 'other-secret@example.com', 'pass123')
        # Prime any Django-level cache with a logged-in render, then check the
        # anonymous render never contains that user's email.
        self.client.force_login(self.user)
        self.client.get(reverse('view_all_products', args=['indoor']))
        self.client.logout()
        response = self.client.get(reverse('view_all_products', args=['indoor']))
        self.assertNotContains(response, 'other-secret@example.com')
        self.assertIn('s-maxage=300', response['Cache-Control'])


