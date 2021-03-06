import json

from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import User
from ..models import Identifier
from ..views import identifier_detail


class IndexViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           password='rubySlippers')

    def test_index_page(self):

        url = reverse('inv_index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')),
                        "index should not be available without logging in")

        self.client.force_login(self.usr)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, 'inventory/index.html')


class ShelvesViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           password='rubySlippers')

    def test_shelves_page(self):

        url = reverse('shelves')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')),
                        "shelves should not be available without logging in")

        self.client.force_login(self.usr)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, 'inventory/shelves.html')
        return


class SuppliersViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           password='rubySlippers')

    def test_suppliers_page(self):

        url = reverse('suppliers')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')),
                        "shelves should not be available without logging in")

        self.client.force_login(self.usr)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, 'inventory/suppliers.html')


class ItemTemplatesViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           password='rubySlippers')

    def test_itemTemplate_page(self):

        url = reverse('itemTemplates')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')),
                        "itemTemplates should not be available without logging in")

        self.client.force_login(self.usr)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, 'inventory/itemTemplate.html')


class IdentifierAPITest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.rf = RequestFactory()
        cls.id = Identifier.idents.create(barcode='1007')

    def test_get_identifier(self):
        pk = '1007'
        url = reverse('identifier-detail', kwargs={'pk': pk})
        req = self.rf.get(url)
        resp = identifier_detail(req, pk)
        self.assertIsInstance(resp, JsonResponse, "should be a JsonResponse")
        d = json.loads(resp.content)
        self.assertNotIn('error', d, "response should succeed")
