from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from products.models import Product, Order, OrderItem
from products.pdf_generator import generate_invoice_pdf
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
            total_amount=Decimal('10000.00'),
            order_status='PLACED'
        )
        OrderItem.objects.create(
            order=order1,
            product=self.product,
            product_name=self.product.name,
            quantity=1,
            unit_price=self.product.price,
            subtotal=self.product.price
        )
        
        # Create second order
        order2 = Order.objects.create(
            user=self.user,
            customer_name='Jane Smith',
            shipping_address='456 Park Ave, Mumbai',
            total_amount=Decimal('20000.00'),
            order_status='PLACED'
        )
        OrderItem.objects.create(
            order=order2,
            product=self.product,
            product_name=self.product.name,
            quantity=2,
            unit_price=self.product.price,
            subtotal=Decimal('20000.00')
        )
        
        # Assert sequential order numbers
        self.assertEqual(order1.order_no, 'ORD-00001')
        self.assertEqual(order2.order_no, 'ORD-00002')
        self.assertEqual(order1.total_amount, Decimal('10000.00'))
        
    def test_pdf_generation(self):
        order = Order.objects.create(
            user=self.user,
            customer_name='John Doe',
            shipping_address='123 Main St, New Delhi',
            total_amount=Decimal('10000.00'),
            order_status='PLACED'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            quantity=1,
            unit_price=self.product.price,
            subtotal=self.product.price
        )
        
        pdf_bytes = generate_invoice_pdf(order)
        self.assertTrue(len(pdf_bytes) > 0)
        # Verify PDF magic signature
        self.assertEqual(pdf_bytes[:4], b'%PDF')

    def test_order_status_action_next_and_cancel(self):
        # Create admin user
        admin = User.objects.create_user(username='admin@gmail.com', email='admin@gmail.com', password='123', is_staff=True)
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
        admin = User.objects.create_user(username='return_admin', password='123', is_staff=True)
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
        admin = User.objects.create_user(username='admin_staff', email='admin@gmail.com', password='123', is_staff=True)
        self.client.force_login(admin)

        response = self.client.get('/admin-panel/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/admin/orders/')
        self.assertEqual(response.status_code, 200)

    def test_admin_cannot_access_cart_or_checkout(self):
        admin = User.objects.create_user(username='store_admin', password='123', is_staff=True)
        self.client.force_login(admin)

        self.assertRedirects(self.client.get(reverse('cart')), reverse('admin_dashboard'))
        self.assertRedirects(self.client.get(reverse('checkout')), reverse('admin_dashboard'))

