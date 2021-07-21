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

class LocIdResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        cls.locID = Identifier.idents.create(barcode='1007')
        Identifier.idents.create(barcode='1000000')

    def test_list(self):
        url = reverse('locid-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('barcode', each, "should be Identifier record")
            self.assertEquals(len(each['barcode']), Identifier.LOC_LEN,
                              "found non-LocID record")

    def test_detail(self):
        bc = self.locID.barcode
        url = reverse('locid-detail', kwargs={'pk': bc})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200, "should return a locID")
        d = json.loads(response.content)
        self.assertIn('barcode', d, "key field missing")
        self.assertEquals(d['barcode'], bc, "wrong locID record found")

    def test_create(self):
        url = reverse('locid-list')
        response = self.client.post(url, {'type': 'loc'})
        self.assertEquals(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'type': 'loc'})
        self.assertEquals(response.status_code, 201, "should return 'Created'")
        d = json.loads(response.content)
        self.assertIn('barcode', d, "key field missing")
