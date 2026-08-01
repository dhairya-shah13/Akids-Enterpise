from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from products.models import Product, Order, OrderItem
from products.pdf_generator import generate_invoice_pdf
from products.utils import calculate_gst
from decimal import Decimal

class OrderManagementTestCase(TestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(username='customer@gmail.com', email='customer@gmail.com', password='password123')
        
        # Create product
        self.product = Product.objects.create(
            name='Test Slide',
            price=Decimal('10000.00'),
            description='Safe test slide',
            stock=10,
            sku='TEST-01'
        )

    def test_order_creation_and_no(self):
        # Create first order
        order1 = Order.objects.create(
            user=self.user,
            customer_name='John Doe',
            shipping_address='123 Main St, New Delhi',
            order_status='PLACED'
        )
        OrderItem.objects.create(
            order=order1,
            product=self.product,
            product_name=self.product.name,
            quantity=1,
            unit_price=self.product.price,
        )
        
        # Create second order
        order2 = Order.objects.create(
            user=self.user,
            customer_name='Jane Smith',
            shipping_address='456 Park Ave, Mumbai',
            order_status='PLACED'
        )
        OrderItem.objects.create(
            order=order2,
            product=self.product,
            product_name=self.product.name,
            quantity=2,
            unit_price=self.product.price,
        )
        
        # Assert sequential order numbers
        self.assertEqual(order1.order_no, 'ORD-00001')
        self.assertEqual(order2.order_no, 'ORD-00002')

    def test_gst_exclusive_math_stored_on_order(self):
        """Business rule: prices are GST-exclusive; 18% GST added on top."""
        order = Order.objects.create(
            user=self.user,
            customer_name='John Doe',
            shipping_address='123 Main St, New Delhi',
            order_status='PLACED'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            quantity=2,
            unit_price=self.product.price,  # 10000 x 2 = 20000 pre-tax
        )
        order.refresh_from_db()
        self.assertEqual(order.subtotal_amount, Decimal('20000.00'))
        self.assertEqual(order.gst_amount, Decimal('3600.00'))
        self.assertEqual(order.total_amount, Decimal('23600.00'))
        self.assertEqual(order.total_amount, order.subtotal_amount * Decimal('1.18'))

    def test_calculate_gst_utility_matches_checkout_contract(self):
        """calculate_gst is the single source of truth used by checkout and PDF."""
        tax = calculate_gst(Decimal('10000.00'))
        self.assertEqual(tax['subtotal'], Decimal('10000.00'))
        self.assertEqual(tax['gst'], Decimal('1800.00'))
        self.assertEqual(tax['cgst'], Decimal('900.00'))
        self.assertEqual(tax['sgst'], Decimal('900.00'))
        self.assertEqual(tax['total'], Decimal('11800.00'))
        # cgst + sgst == gst exactly
        self.assertEqual(tax['cgst'] + tax['sgst'], tax['gst'])

    def test_pdf_invoice_gst_matches_order(self):
        """PDF invoice must show the same GST-exclusive numbers as the order."""
        order = Order.objects.create(
            user=self.user,
            customer_name='John Doe',
            shipping_address='123 Main St, New Delhi',
            order_status='PLACED'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            quantity=1,
            unit_price=self.product.price,
        )
        order.refresh_from_db()

        pdf_bytes = generate_invoice_pdf(order)
        self.assertTrue(len(pdf_bytes) > 0)
        self.assertEqual(pdf_bytes[:4], b'%PDF')
        # PDF is compressed; extract text via a simple FlateDecode pass.
        text = self._extract_pdf_text(pdf_bytes)
        self.assertIn('10,000.00', text)  # taxable amount
        self.assertIn('900.00', text)     # CGST
        self.assertIn('11,800.00', text)  # total incl. GST
        # No inclusive/divergent math: total == subtotal * 1.18 shown in PDF
        self.assertEqual(order.total_amount, Decimal('11800.00'))

    def _extract_pdf_text(self, pdf_bytes):
        """Extract text from a ReportLab-generated PDF.

        ReportLab (>=4) emits content streams that are ASCII85-encoded and
        zlib-compressed (an embedded JPEG logo stream is also present, which we
        skip via the JFIF magic check).
        """
        import re, zlib, base64
        texts = []
        for m in re.finditer(rb'stream\r?\n(.*?)endstream', pdf_bytes, re.DOTALL):
            data = m.group(1).strip(b'\r\n')
            try:
                data = base64.a85decode(data, adobe=True)
            except Exception:
                continue
            # Skip non-text streams (e.g. the embedded JPEG logo).
            if data[:3] == b'\xff\xd8\xff':
                continue
            try:
                data = zlib.decompress(data)
            except Exception:
                continue
            for tm in re.finditer(rb'\(((?:[^()\\]|\\.)*)\)\s*Tj', data):
                texts.append(tm.group(1).decode('latin-1', errors='replace'))
        return ' '.join(texts)

    def test_pdf_generation(self):
        order = Order.objects.create(
            user=self.user,
            customer_name='John Doe',
            shipping_address='123 Main St, New Delhi',
            order_status='PLACED'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            quantity=1,
            unit_price=self.product.price,
        )
        
        pdf_bytes = generate_invoice_pdf(order)
        self.assertTrue(len(pdf_bytes) > 0)
        # Verify PDF magic signature
        self.assertEqual(pdf_bytes[:4], b'%PDF')

    def test_order_success_idor_cross_user_404(self):
        """User A's order must 404 for User B (no existence leak)."""
        other_user = User.objects.create_user(username='other@gmail.com', email='other@gmail.com', password='password123')
        order = Order.objects.create(
            user=self.user,
            customer_name='John Doe',
            shipping_address='123 Main St',
            order_status='PLACED'
        )
        OrderItem.objects.create(order=order, product=self.product, product_name=self.product.name, quantity=1, unit_price=self.product.price)

        # User B cannot see User A's order
        self.client.force_login(other_user)
        response = self.client.get(reverse('order_success', args=[order.pk]))
        self.assertEqual(response.status_code, 404)

    def test_invoice_cross_user_404_not_403(self):
        """The invoice endpoint must 404 (not 403) for cross-user access so
        order existence is never leaked — same ownership pattern as order_success."""
        other_user = User.objects.create_user(username='other2@gmail.com', email='other2@gmail.com', password='password123')
        order = Order.objects.create(
            user=self.user,
            customer_name='John Doe',
            shipping_address='123 Main St',
            order_status='PLACED'
        )
        OrderItem.objects.create(order=order, product=self.product, product_name=self.product.name, quantity=1, unit_price=self.product.price)

        self.client.force_login(other_user)
        response = self.client.get(reverse('api_admin_order_invoice', args=[order.pk]))
        self.assertEqual(response.status_code, 404)

    def test_invoice_owner_can_download(self):
        """The order owner can download their own invoice (200 PDF)."""
        order = Order.objects.create(
            user=self.user,
            customer_name='John Doe',
            shipping_address='123 Main St',
            order_status='PLACED'
        )
        OrderItem.objects.create(order=order, product=self.product, product_name=self.product.name, quantity=1, unit_price=self.product.price)

        self.client.force_login(self.user)
        response = self.client.get(reverse('api_admin_order_invoice', args=[order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        # Anonymous user cannot see it either
        self.client.logout()
        response = self.client.get(reverse('order_success', args=[order.pk]))
        self.assertEqual(response.status_code, 404)

        # Owner can see it
        self.client.force_login(self.user)
        response = self.client.get(reverse('order_success', args=[order.pk]))
        self.assertEqual(response.status_code, 200)

    def test_order_success_idor_admin_can_view_any(self):
        """Admins may view any order via the same view (consistent with invoice)."""
        admin = User.objects.create_user(username='staff_admin', email='staff@example.com', password='pass123', is_staff=True)
        order = Order.objects.create(
            user=self.user,
            customer_name='John Doe',
            shipping_address='123 Main St',
            order_status='PLACED'
        )
        OrderItem.objects.create(order=order, product=self.product, product_name=self.product.name, quantity=1, unit_price=self.product.price)
        self.client.force_login(admin)
        response = self.client.get(reverse('order_success', args=[order.pk]))
        self.assertEqual(response.status_code, 200)

    def test_order_status_action_next_and_cancel(self):
        # Create admin user
        admin = User.objects.create_user(username='admin_user', email='admin@example.com', password='pass123', is_staff=True)
        self.client.force_login(admin)

        order = Order.objects.create(
            user=self.user,
            customer_name='Action Customer',
            shipping_address='789 Test Rd',
            order_status='PLACED'
        )

        # Advance status via action="next" -> CONFIRMED
        response = self.client.post(
            f"/api/admin/orders/{order.id}/status/",
            data='{"action": "next"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'CONFIRMED')

        # Cancel status via action="cancel" -> CANCELLED
        response = self.client.post(
            f"/api/admin/orders/{order.id}/status/",
            data='{"action": "cancel"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'CANCELLED')

    def test_delivered_order_can_be_returned(self):
        admin = User.objects.create_user(username='return_admin', password='pass123', is_staff=True)
        self.client.force_login(admin)
        order = Order.objects.create(
            user=self.user,
            customer_name='Return Customer',
            shipping_address='789 Test Rd',
            order_status='DELIVERED'
        )

        response = self.client.post(
            f"/api/admin/orders/{order.id}/status/",
            data='{"status": "RETURNED"}',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'RETURNED')

    def test_admin_access_control(self):
        # Regular customer access should be forbidden
        self.client.force_login(self.user)
        response = self.client.get('/admin-panel/')
        self.assertEqual(response.status_code, 302) # redirects to login

        response = self.client.get('/api/admin/orders/')
        self.assertEqual(response.status_code, 403)

        # Admin user access should be allowed
        admin = User.objects.create_user(username='admin_staff', email='staff2@example.com', password='pass123', is_staff=True)
        self.client.force_login(admin)

        response = self.client.get('/admin-panel/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/admin/orders/')
        self.assertEqual(response.status_code, 200)

    def test_admin_cannot_access_cart_or_checkout(self):
        admin = User.objects.create_user(username='store_admin', password='pass123', is_staff=True)
        self.client.force_login(admin)

        self.assertRedirects(self.client.get(reverse('cart')), reverse('admin_dashboard'))
        self.assertRedirects(self.client.get(reverse('checkout')), reverse('admin_dashboard'))

    def test_checkout_total_equals_subtotal_times_1_18(self):
        """End-to-end: POST /checkout/ must produce total == subtotal * 1.18."""
        self.client.force_login(self.user)
        # Put 3 x 10000 = 30000 in the cart
        session = self.client.session
        session['cart'] = {str(self.product.pk): 3}
        session.save()

        response = self.client.post(reverse('checkout'), {
            'customer_name': 'John Doe',
            'shipping_address': '123 Main St, New Delhi',
        })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.latest('id')
        self.assertEqual(order.subtotal_amount, Decimal('30000.00'))
        self.assertEqual(order.gst_amount, Decimal('5400.00'))
        self.assertEqual(order.total_amount, Decimal('35400.00'))
        self.assertEqual(order.total_amount, order.subtotal_amount * Decimal('1.18'))
