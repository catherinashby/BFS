import json
import sys
from io import StringIO
from contextlib import contextmanager

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from ..models import Identifier, Location, Supplier, ItemTemplate, Picture
from ..models import StockBook, Price, Invoice, Purchase


@contextmanager
def capture(command, *args, **kwargs):
    out, sys.stdout = sys.stdout, StringIO()
    try:
        command(*args, **kwargs)
        sys.stdout.seek(0)
        yield sys.stdout.read()
    finally:
        sys.stdout = out


class IdentResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Identifier.idents.create(barcode='1007')
        Identifier.idents.create(barcode='1010')
        Identifier.idents.create(barcode='1000002', linked_code='0006151620418')
        Identifier.idents.create(barcode='1000015')

    def test_auth(self):
        digitstring = ' '
        url = reverse('ident-detail', kwargs={'digitstring': digitstring})
        response = self.client.post(url, {'barcode': 999},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

    def test_detail(self):
        digitstring = ' '
        url = reverse('ident-detail', kwargs={'digitstring': digitstring})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return 'OK'")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('digitstring', d['errors'], "digitstriing error missing")
        self.assertEqual(d['errors']['digitstring'], "Must be a string of digits")

        digitstring = '999'
        url = reverse('ident-detail', kwargs={'digitstring': digitstring})
        response = self.client.get(url)
        d = json.loads(response.content)
        self.assertIn('type', d, "type field missing")
        self.assertEqual(d['type'], "OTHER", "Wrong typecode")

        digitstring = '1007'
        url = reverse('ident-detail', kwargs={'digitstring': digitstring})
        response = self.client.get(url)
        d = json.loads(response.content)
        self.assertIn('type', d, "type field missing")
        self.assertEqual(d['type'], "LOC", "Wrong typecode")

        digitstring = '1000015'
        url = reverse('ident-detail', kwargs={'digitstring': digitstring})
        response = self.client.get(url)
        d = json.loads(response.content)
        self.assertIn('type', d, "type field missing")
        self.assertEqual(d['type'], "ITM", "Wrong typecode")

        digitstring = '0006151620418'
        url = reverse('ident-detail', kwargs={'digitstring': digitstring})
        response = self.client.get(url)
        d = json.loads(response.content)
        self.assertIn('type', d, "type field missing")
        self.assertEqual(d['type'], "ITM", "Wrong typecode")


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
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('barcode', each, "should be Identifier record")
            self.assertEqual(len(each['barcode']), Identifier.LOC_LEN,
                             "found non-LocID record")

    def test_detail(self):
        bc = self.locID.barcode
        url = reverse('locid-detail', kwargs={'pk': bc})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a locID")
        d = json.loads(response.content)
        self.assertIn('barcode', d, "key field missing")
        self.assertEqual(d['barcode'], bc, "wrong locID record found")

    def test_create(self):
        url = reverse('locid-list')
        response = self.client.post(url, {'barcode': 1055},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'barcode': 1055},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 201, "should return 'Created'")


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
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('name', each, "should have name field")

    def test_detail(self):
        pk = 1010
        id = reverse('identifier-detail', kwargs={'pk': pk})
        url = reverse('location-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a location")
        d = json.loads(response.content)
        self.assertIn('name', d, "key field missing")
        self.assertEqual(d['locID'], id, "wrong locID record found")

    def test_create(self):
        url = reverse('location-list')
        response = self.client.post(url, {'name': 'shelf'},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'description': ''},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('name', d['errors'], "name error missing")
        self.assertEqual(d['errors']['name'], "A name is required")

        response = self.client.post(url, {'name': 'shelf', 'description': ''},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 201, "should return 'Created'")

        response = self.client.post(url, {'name': 'shelf', 'description': ''},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('name', d['errors'], "name error missing")
        self.assertEqual(d['errors']['name'], "Name already used -- pick another")

    def test_update(self):
        pk = 1010
        change = json.dumps({'description': ''})
        url = reverse('location-detail', kwargs={'pk': pk})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")

        change = json.dumps({'name': 'Basket'})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")

        change = json.dumps({'name': 'Shelf A-2'})
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('name', d['errors'], "name error missing")
        self.assertEqual(d['errors']['name'], "Name already used -- pick another")

    def test_print_label(self):
        pk = 1010
        change = json.dumps({'printed': True})
        url = reverse('location-detail', kwargs={'pk': pk})

        def test_patch(url, change):
            response = self.client.patch(url, change)
            self.assertEqual(response.status_code, 200, "should return 'OK'")

        with capture(test_patch, url, change) as output:
            self.assertEqual(output,
                             'Printing barcode label for Location "Basket 1"\n',
                             "Expected dummy print statement")


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
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('name', each, "should have name field")

    def test_detail(self):
        pk = 2
        url = reverse('supplier-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a supplier")
        d = json.loads(response.content)
        self.assertIn('name', d, "key field missing")

    def test_create(self):
        url = reverse('supplier-list')
        response = self.client.post(url, {'name': 'Foust Textiles'},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'description': ''},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('name', d['errors'], "name error missing")
        self.assertEqual(d['errors']['name'], "A name is required")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'name': 'Foust Textiles',
                                          'city': 'Kings Mountain',
                                          'state': 'North Carolina',
                                          'zip5': '28086'},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 201, "should return 'Created'")

        response = self.client.post(url, {'name': 'Foust Textiles'},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('name', d['errors'], "name error missing")
        self.assertEqual(d['errors']['name'], "Name already used -- pick another")

    def test_update(self):
        pk = 1
        change = json.dumps({'city': 'Nashua', 'state': 'New Hampshire'})
        url = reverse('supplier-detail', kwargs={'pk': pk})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")

        change = json.dumps({'name': 'New England Quilt Supply'})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")

        change = json.dumps({'name': 'Fabric Mart'})
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('name', d['errors'], "name error missing")
        self.assertEqual(d['errors']['name'], "Name already used -- pick another")


class ItemTemplateResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        Identifier.idents.create(barcode='1007')
        cls.itmID = Identifier.idents.create(barcode='1000015')
        ItemTemplate.objects.create(description='Yellow Brick Road', identifier=cls.itmID)
        ItemTemplate.objects.create(description='Emerald City',
                                    identifier=Identifier.idents.create(barcode='1000002'))
        ItemTemplate.objects.create(description='Fields of Popae',
                                    identifier=Identifier.idents.create(barcode='1000028'))

    def test_list(self):

        url = reverse('item-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('description', each, "should have description field")
        return

    def test_detail(self):

        pk = 1000002
        id = reverse('identifier-detail', kwargs={'pk': pk})
        url = reverse('item-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an item")
        d = json.loads(response.content)
        self.assertIn('description', d, "key field missing")
        self.assertEqual(d['itmID'], id, "wrong itemID record found")

    def test_create(self):

        item = {'brand': 'Windham',
                'content': 'Cotton Fabric',
                'part_unit': 'By the Yard',
                'yardage': True}
        url = reverse('item-list')
        response = self.client.post(url, {'description': 'A La Carte'},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, item, content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('description', d['errors'], "description error missing")
        self.assertEqual(d['errors']['description'], "A description is required")

        item['description'] = 'A La Carte'
        response = self.client.post(url, item, content_type="application/json")
        self.assertEqual(response.status_code, 201, "should return 'Created'")

        response = self.client.post(url, item, content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('description', d['errors'], "description error missing")
        self.assertEqual(d['errors']['description'],
                         "Description already used -- pick another")

        item['linked_code'] = '0006151620418'
        item['description'] = 'Comfort and Joy'
        response = self.client.post(url, item, content_type="application/json")
        self.assertEqual(response.status_code, 201, "should return 'Created'")

    def test_update(self):

        pk = 1000002
        item = {'content': 'Cotton Fabric',
                'part_unit': 'By the Yard'}
        change = json.dumps(item)
        url = reverse('item-detail', kwargs={'pk': pk})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")

        item['linked_code'] = '0006151620418'
        change = json.dumps(item)
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")

        item['brand'] = 'Windham'
        change = json.dumps(item)
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")

        item['description'] = 'Mountains of Mist'
        change = json.dumps(item)
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")

        item['description'] = 'Yellow Brick Road'
        change = json.dumps(item)
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('description', d['errors'], "description error missing")
        self.assertEqual(d['errors']['description'],
                         "Description already used -- pick another")

    def test_print_label(self):

        pk = 1000015
        change = json.dumps({'printed': True})
        url = reverse('item-detail', kwargs={'pk': pk})

        def test_patch(url, change):
            response = self.client.patch(url, change)
            self.assertEqual(response.status_code, 200, "should return 'OK'")

        with capture(test_patch, url, change) as output:
            self.assertEqual(output,
                             'Printing barcode label for Item "Yellow Brick Road"\n',
                             "Expected dummy print statement")


class PictureResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        cls.badID = '1000011'
        cls.itmID = '1000002'
        ItemTemplate.objects.create(description='Small Bitmap',
                                    identifier=Identifier.idents.create(barcode=cls.itmID))
        dataFile = 'inventory/tests/data/small.bmp'
        cls.pic1 = Picture.objects.create(photo=dataFile)
        cls.pic2 = Picture.objects.create(photo=dataFile)
        return

    def test_list(self):
        url = reverse('picture-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('photo', each, "should have photo field")

    def test_detail(self):
        pk = 2
        url = reverse('picture-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a picture")
        d = json.loads(response.content)
        self.assertIn('photo', d, "key field missing")

    def test_update(self):
        pk = 1
        change = json.dumps({'item_id': self.itmID})
        url = reverse('picture-detail', kwargs={'pk': pk})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertIn('item_id', d, "item_id field missing")
        self.assertEqual(d['item_id'], self.itmID, "Item ID should be set")

        change = json.dumps({'item_id': ''})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertIn('item_id', d, "item_id field missing")
        self.assertEqual(d['item_id'], "", "Item ID should be cleared")

        change = json.dumps({'item_id': self.badID})
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('item_id', d['errors'], "item_id error missing")
        self.assertEqual(d['errors']['item_id'], "Not a valid identifier")

        change = json.dumps({'uploaded': 'today'})
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('item_id', d['errors'], "item_id error missing")
        self.assertEqual(d['errors']['item_id'], "No identifier received")


class StockBookResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        cls.locID = '1007'
        cls.itmID = '1000002'
        cls.itm2 = '1000015'
        cls.itm3 = '1000028'
        l1 = Location.objects.create(
                    identifier=Identifier.idents.create(barcode=cls.locID))
        i1 = ItemTemplate.objects.create(
                    description='Bolt of Fabric',
                    identifier=Identifier.idents.create(barcode=cls.itmID))
        i2 = ItemTemplate.objects.create(
                    description='Inventoried Item',
                    yardage=False,
                    identifier=Identifier.idents.create(barcode=cls.itm2))
        ItemTemplate.objects.create(
                    description='Another Item',
                    yardage=False,
                    identifier=Identifier.idents.create(barcode=cls.itm3))
        StockBook.objects.create(itm=i1, loc=l1)

    def test_detail(self):
        url = reverse('stock-detail', kwargs={'pk': 1000})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('itm_id', d['errors'], "itm_id error missing")
        self.assertEqual(d['errors']['itm_id'], "Item not found")

        url = reverse('stock-detail', kwargs={'pk': self.itm2})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('item', d['errors'], "item error missing")
        self.assertEqual(d['errors']['item'], "Record not found")

        url = reverse('stock-detail', kwargs={'pk': self.itmID})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a stock record")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('itm', d, "itm field missing")
        self.assertEqual(d['itm'], self.itmID)
        return

    def test_list(self):

        url = reverse('stock-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('created', each, "should have 'created' field")
        return

    def test_create(self):
        url = reverse('stock-list')
        response = self.client.post(url, {'item': 'record'},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'item': 'record'},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('itm_id', d['errors'], "itm_id error missing")
        self.assertEqual(d['errors']['itm_id'], "No item ID received")

        response = self.client.post(url, {'itm_id': '1234567'},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('itm_id', d['errors'], "itm_id error missing")
        self.assertEqual(d['errors']['itm_id'], "Item not found")

        response = self.client.post(url, {'itm_id': self.itmID},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('itm_id', d['errors'], "itm_id error missing")
        self.assertEqual(d['errors']['itm_id'], "Record already exists")

        response = self.client.post(url, {'itm_id': self.itm2, 'loc_id': 'far'},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('loc_id', d['errors'], "loc_id error missing")
        self.assertEqual(d['errors']['loc_id'], "Location not found")

        response = self.client.post(url, {'itm_id': self.itm2, 'loc_id': self.locID},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('created', d, "'created' field missing")

        response = self.client.post(url, {'itm_id': self.itm3, 'units': 4},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('units', d, "units field missing")

        return

    def test_update(self):

        url = reverse('stock-detail', kwargs={'pk': 1000})
        response = self.client.put(url, 'Invalid item ID')
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.put(url, '{"itm_id": 1000}')
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('itm_id', d['errors'], "itm_id error missing")
        self.assertEqual(d['errors']['itm_id'], "Item not found")

        url = reverse('stock-detail', kwargs={'pk': self.itm2})
        response = self.client.put(url, '{"loc_id": 42}')
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('loc_id', d['errors'], "loc error missing")
        self.assertEqual(d['errors']['loc_id'], "Location not found")

        url = reverse('stock-detail', kwargs={'pk': self.itm2})
        change = json.dumps({'loc_id': self.locID, 'eighths': 4})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('eighths', d, "eighths field missing")
        self.assertIsNone(d['eighths'], "Eighths should be unset")

        url = reverse('stock-detail', kwargs={'pk': self.itmID})
        change = json.dumps({'eighths': 4, 'units': 24})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('eighths', d, "eighths field missing")
        self.assertEqual(d['eighths'], 4, "Eighths should be set")

        return


class PriceResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        cls.itmID = '1000002'
        cls.itm2 = '1000015'
        cls.amount = 7.99
        i1 = ItemTemplate.objects.create(
                    description='Bolt of Fabric',
                    identifier=Identifier.idents.create(barcode=cls.itmID))
        i2 = ItemTemplate.objects.create(
                    description='Inventoried Item',
                    yardage=False,
                    identifier=Identifier.idents.create(barcode=cls.itm2))
        Price.objects.create(itm=i1, price=cls.amount)
        return

    def test_detail(self):
        url = reverse('price-detail', kwargs={'pk': 1000})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('itm_id', d['errors'], "itm_id error missing")
        self.assertEqual(d['errors']['itm_id'], "Item not found")

        url = reverse('price-detail', kwargs={'pk': self.itm2})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('item', d['errors'], "item error missing")
        self.assertEqual(d['errors']['item'], "Record not found")

        url = reverse('price-detail', kwargs={'pk': self.itmID})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a price record")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('itm', d, "itm field missing")
        self.assertEqual(d['itm'], self.itmID)
        self.assertEqual(d['price'], '{}'.format(self.amount))
        return

    def test_update(self):

        url = reverse('price-detail', kwargs={'pk': 1000})
        response = self.client.put(url, 'Invalid item ID')
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.put(url, '{"itm_id": 1000}')
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('itm_id', d['errors'], "itm_id error missing")
        self.assertEqual(d['errors']['itm_id'], "Item not found")

        url = reverse('price-detail', kwargs={'pk': self.itm2})
        change = json.dumps({'discount': 10})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('price', d, "price field missing")
        self.assertIsNone(d['price'], "price field set")

        url = reverse('price-detail', kwargs={'pk': self.itm2})
        amount = '0.99'
        change = json.dumps({'price': amount})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('price', d, "price field missing")
        self.assertEqual(d['price'], amount)

        return


class InvoiceResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        sup1 = Supplier.objects.create(name='Milltown')
        sup2 = Supplier.objects.create(name='Bedoses Fabric')
        inv101 = Invoice.objects.create(id=101, vendor=sup1)
        return

    def test_detail(self):

        url = reverse('invoice-detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('id', d['errors'], "id error missing")
        self.assertEqual(d['errors']['id'], "Invoice #1 not found")

        url = reverse('invoice-detail', kwargs={'pk': 101})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an invoice")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('id', d, "id field missing")
        self.assertIn('vendor', d, "vendor field missing")
        self.assertEqual(d['id'], 101)

    def test_create(self):

        url = reverse('invoice-list')
        response = self.client.post(url, {'name': 'Choice Fabrics'},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'supplier': 11},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('vendor_id', d['errors'], "vendor_id error missing")
        self.assertEqual(d['errors']['vendor_id'], "A supplier is required")

        response = self.client.post(url, {'vendor_id': 11},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('vendor_id', d['errors'], "vendor_id error missing")
        self.assertEqual(d['errors']['vendor_id'], "Supplier not found")

        response = self.client.post(url, {'vendor_id': 2},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('id', d, "id field missing")
        self.assertIn('received', d, "received field missing")
        self.assertEqual(d['id'], 102)


class PurchaseResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        sup1 = Supplier.objects.create(name='Milltown')
        sup2 = Supplier.objects.create(name='Bedoses Fabric')
        inv101 = Invoice.objects.create(id=101, vendor=sup1)
        inv102 = Invoice.objects.create(id=102, vendor=sup2)
        itm2 = ItemTemplate.objects.create(
                    description='Emerald City',
                    identifier=Identifier.idents.create(barcode='1000002'))
        itm28 = ItemTemplate.objects.create(
                    description='Fields of Popae',
                    identifier=Identifier.idents.create(barcode='1000028'))
        cls.pchs = Purchase.objects.create(invoice=inv101, item=itm2)
        cls.inv2 = inv102
        cls.itm28 = itm28

    def test_detail(self):

        url = reverse('purchase-detail', kwargs={'pk': 3})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('id', d['errors'], "id error missing")
        self.assertEqual(d['errors']['id'], "Purchase #3 not found")

        url = reverse('purchase-detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an order")
        d = json.loads(response.content)
        self.assertIn('invoice', d, "invoice id missing")
        self.assertEqual(d['invoice'], self.pchs.invoice_id)
        self.assertIn('item', d, "item id missing")
        self.assertEqual(d['item'], self.pchs.item_id)

    def test_create(self):

        order = {'invoice_id': 99,
                 'item_id': '1000015'}
        url = reverse('purchase-list')
        response = self.client.post(url, {'purchase': 'order'},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'purchase': 'order'},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('invoice_id', d['errors'], "invoice_id error missing")
        self.assertEqual(d['errors']['invoice_id'], "An invoice is required")
        self.assertIn('item_id', d['errors'], "item_id error missing")
        self.assertEqual(d['errors']['item_id'], "An item is required")

        response = self.client.post(url, order,
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('invoice_id', d['errors'], "invoice_id error missing")
        self.assertEqual(d['errors']['invoice_id'],
                         'Invoice #{} not found'.format(order['invoice_id']))
        self.assertIn('item_id', d['errors'], "item_id error missing")
        self.assertEqual(d['errors']['item_id'],
                         'Item {} not found'.format(order['item_id']))

        order['invoice_id'] = self.inv2.id
        order['item_id'] = self.itm28.identifier_id
        response = self.client.post(url, order,
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertEqual(d['invoice'], order['invoice_id'])
        self.assertEqual(d['item'], order['item_id'])

        order['cost'] = 'cash'
        response = self.client.post(url, order,
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertEqual(d['invoice'], order['invoice_id'])
        self.assertEqual(d['item'], order['item_id'])

        order['invoice_id'] = self.pchs.invoice_id
        order['item_id'] = self.pchs.item_id
        order['cost'] = '12.99'
        response = self.client.post(url, order,
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertEqual(d['invoice'], order['invoice_id'])
        self.assertEqual(d['item'], order['item_id'])
        self.assertEqual(d['cost'], order['cost'])
