import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import Product, Inquiry, InquiryLineItem

class InquiryTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Seed test products
        self.p1 = Product.objects.create(
            name="Everest Indoor Slide",
            category="INDOORS",
            price=15000.00,
            sku="LFI-IND-EVEREST",
            stock=5
        )
        self.p2 = Product.objects.create(
            name="Adventure Outdoor Swings",
            category="OUTDOORS",
            price=25000.00,
            sku="LFI-OUT-ADVENTURE",
            stock=3
        )

    def test_submit_valid_catalog_inquiry(self):
        url = reverse('submit_catalog_inquiry')
        payload = {
            "name": "Rajesh Kumar",
            "phone_number": "+91 99243 43003",
            "email": "rajesh@gmail.com",
            "module": "indoor",
            "line_items": [
                { "product_code": "LFI-IND-EVEREST", "quantity": 2 },
                { "product_code": "LFI-OUT-ADVENTURE", "quantity": 1 }
            ]
        }
        
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify db persistence
        inquiry = Inquiry.objects.get(pk=data['inquiry_id'])
        self.assertEqual(inquiry.name, "Rajesh Kumar")
        self.assertEqual(inquiry.contact_number, "+91 99243 43003")
        self.assertEqual(inquiry.email, "rajesh@gmail.com")
        self.assertEqual(inquiry.module, "indoor")
        self.assertEqual(inquiry.status, "NEW")
        
        line_items = inquiry.line_items.all()
        self.assertEqual(line_items.count(), 2)
        self.assertEqual(line_items.filter(product_code="LFI-IND-EVEREST").first().quantity, 2)

    def test_submit_invalid_missing_fields(self):
        url = reverse('submit_catalog_inquiry')
        payload = {
            "name": "",  # missing name
            "phone_number": "+91 99243 43003",
            "email": "rajesh@gmail.com",
            "module": "indoor",
            "line_items": [
                { "product_code": "LFI-IND-EVEREST", "quantity": 2 }
            ]
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn("required", data['error'])

    def test_inquiry_number_generation(self):
        inq1 = Inquiry.objects.create(name="Customer 1", contact_number="1234567890", module="indoor")
        inq2 = Inquiry.objects.create(name="Customer 2", contact_number="0987654321", module="outdoor")

        self.assertTrue(inq1.inquiry_no.startswith("INQ-"))
        self.assertTrue(inq2.inquiry_no.startswith("INQ-"))
        self.assertNotEqual(inq1.inquiry_no, inq2.inquiry_no)

    def test_api_admin_inquiries_search_and_filter(self):
        from django.contrib.auth.models import User
        admin = User.objects.create_user(username='admin@gmail.com', email='admin@gmail.com', password='123', is_staff=True)
        self.client.force_login(admin)

        inq1 = Inquiry.objects.create(name="Aarav Sharma", contact_number="11111", email="aarav@test.com", module="indoor", status="NEW")
        InquiryLineItem.objects.create(inquiry=inq1, product_code="LFI-IND-EVEREST", product_name="Everest Indoor Slide", quantity=1)

        inq2 = Inquiry.objects.create(name="Bhavna Patel", contact_number="22222", email="bhavna@test.com", module="outdoor", status="CONTACTED")

        # Test name search
        resp = self.client.get("/api/admin/inquiries/?q=Aarav")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['inquiries']), 1)
        self.assertEqual(data['inquiries'][0]['customer_name'], "Aarav Sharma")
        self.assertEqual(data['inquiries'][0]['inquiry_no'], inq1.inquiry_no)

        # Test product search
        resp = self.client.get("/api/admin/inquiries/?q=Everest")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['inquiries']), 1)

        # Test module filter
        resp = self.client.get("/api/admin/inquiries/?module=outdoor")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['inquiries']), 1)
        self.assertEqual(data['inquiries'][0]['customer_name'], "Bhavna Patel")

    def test_whatsapp_integration(self):
        url = reverse('submit_catalog_inquiry')
        payload = {
            "name": "Dev Test",
            "phone_number": "9924343003",
            "email": "test@test.com",
            "module": "indoor",
            "line_items": [
                { "product_code": "LFI-01", "quantity": 3 }
            ]
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('whatsapp_url', data)
        self.assertTrue(data['whatsapp_url'].startswith('https://wa.me/919924343003?text='))
        
        # Verify text elements are URL-encoded properly
        import urllib.parse
        decoded = urllib.parse.unquote(data['whatsapp_url'])
        self.assertIn("Hello Akids Enterprise", decoded)
        self.assertIn("3x LFI-01", decoded)
        self.assertIn("Dev Test", decoded)
        self.assertNotIn("Inquiry No", decoded)

    def test_admin_can_close_inquiry_and_view_customer_history(self):
        from django.contrib.auth.models import User
        admin = User.objects.create_user(username='inquiry_admin', password='123', is_staff=True)
        self.client.force_login(admin)
        previous = Inquiry.objects.create(
            name='Mukesh', contact_number='1234567890', email='mukesh@example.com', module='indoor'
        )
        InquiryLineItem.objects.create(inquiry=previous, product_code='LFI-01', quantity=2)
        inquiry = Inquiry.objects.create(
            name='Mukesh', contact_number='1234567890', email='mukesh@example.com', module='outdoor'
        )

        response = self.client.post(
            reverse('api_admin_inquiry_close', args=[inquiry.pk]),
            data='{"outcome": "WON"}',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, 'CLOSED')
        self.assertEqual(inquiry.closure_outcome, 'WON')

        closed = self.client.get(reverse('api_admin_closed_inquiries')).json()
        self.assertEqual(closed['won'][0]['id'], inquiry.id)

        detail = self.client.get(reverse('api_admin_inquiry_detail', args=[inquiry.pk])).json()
        self.assertEqual(detail['previous_inquiries'][0]['inquiry_no'], previous.inquiry_no)
        self.assertEqual(detail['previous_inquiries'][0]['items'], ['2x LFI-01'])


