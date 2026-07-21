from django.test import TestCase
from django.urls import reverse


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


class MRSportsTests(TestCase):
    def test_mr_sports_page_uses_its_new_name_and_olive_background(self):
        response = self.client.get(reverse('rfsports'))

        self.assertContains(response, 'MR Sports')
        self.assertContains(response, 'background-color: #e7e9cf')
