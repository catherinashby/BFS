import json
import sys
from io import StringIO
from contextlib import contextmanager

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from ..models import Identifier, Location, Supplier


@contextmanager
def capture(command, *args, **kwargs):
    out, sys.stdout = sys.stdout, StringIO()
    try:
        command(*args, **kwargs)
        sys.stdout.seek(0)
        yield sys.stdout.read()
    finally:
        sys.stdout = out


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
        response = self.client.post(url, {'barcode': 1055},
                                    content_type="application/json")
        self.assertEquals(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'barcode': 1055},
                                    content_type="application/json")
        self.assertEquals(response.status_code, 201, "should return 'Created'")


class LocationResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        cls.locID = Identifier.idents.create(barcode='1007')
        Identifier.idents.create(barcode='1000000')
        cls.loc = Location.objects.create(name='Shelf A-1',
                                          identifier=Identifier.idents.create(barcode='1000'),
                                          description='Top shelf, first rack')
        Location.objects.create(name='Shelf A-2', identifier=cls.locID)
        Location.objects.create(name='Basket 1',
                                identifier=Identifier.idents.create(barcode='1010'),
                                description='On table next to desk')

    def test_list(self):
        url = reverse('location-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('name', each, "should have name field")

    def test_detail(self):
        pk = 1010
        id = reverse('identifier-detail', kwargs={'pk': pk})
        url = reverse('location-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200, "should return a location")
        d = json.loads(response.content)
        self.assertIn('name', d, "key field missing")
        self.assertEquals(d['locID'], id, "wrong locID record found")

    def test_create(self):
        url = reverse('location-list')
        response = self.client.post(url, {'name': 'shelf'},
                                    content_type="application/json")
        self.assertEquals(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'name': 'shelf', 'description': ''},
                                    content_type="application/json")
        self.assertEquals(response.status_code, 201, "should return 'Created'")

    def test_update(self):
        pk = 1010
        change = json.dumps({'description': ''})
        url = reverse('location-detail', kwargs={'pk': pk})
        response = self.client.put(url, change)
        self.assertEquals(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.put(url, change)
        self.assertEquals(response.status_code, 202, "should return 'Accepted'")

        return

    def test_print_label(self):
        pk = 1010
        change = json.dumps({'printed': True})
        url = reverse('location-detail', kwargs={'pk': pk})

        def test_patch(url, change):
            response = self.client.patch(url, change)
            self.assertEquals(response.status_code, 200, "should return 'OK'")

        with capture(test_patch, url, change) as output:
            self.assertEquals(output,
                              'Printing barcode label for Location "Basket 1"\n',
                              "Expected dummy print statement")
        return


class SupplierResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        cls.sup1 = Supplier.objects.create(name='Choice Fabrics')
        cls.sup2 = Supplier.objects.create(name='Fabric Mart')

    def test_list(self):
        url = reverse('supplier-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('name', each, "should have name field")

    def test_detail(self):
        pk = 2
        url = reverse('supplier-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200, "should return a supplier")
        d = json.loads(response.content)
        self.assertIn('name', d, "key field missing")

    def test_create(self):
        url = reverse('supplier-list')
        response = self.client.post(url, {'name': 'Foust Textiles'},
                                    content_type="application/json")
        self.assertEquals(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'name': 'Foust Textiles',
                                          'city': 'Kings Mountain',
                                          'state': 'North Carolina',
                                          'zip5': '28086'},
                                    content_type="application/json")
        self.assertEquals(response.status_code, 201, "should return 'Created'")

    def test_update(self):
        pk = 1
        change = json.dumps({'city': 'Nashua', 'state': 'New Hampshire'})
        url = reverse('supplier-detail', kwargs={'pk': pk})
        response = self.client.put(url, change)
        self.assertEquals(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.put(url, change)
        self.assertEquals(response.status_code, 202, "should return 'Accepted'")

        return
