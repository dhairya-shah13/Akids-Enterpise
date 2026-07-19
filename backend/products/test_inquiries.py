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
