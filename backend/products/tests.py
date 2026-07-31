from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from products.models import Product, UserProfile, Address


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

