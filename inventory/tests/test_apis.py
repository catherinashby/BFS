import copy
import json
import sys

from io import StringIO
from contextlib import contextmanager
from datetime import date, timedelta
from decimal import Decimal
from tempfile import TemporaryDirectory

from django.test import TestCase, RequestFactory
from django.urls import reverse

from accounts.models import User
from ..apis import BaseResource
from ..models import Identifier, Location, Supplier, ItemTemplate, Picture
from ..models import StockBook, Price, Invoice, Purchase, Receipt, ItemSale


@contextmanager
def capture(command, *args, **kwargs):
    out, sys.stdout = sys.stdout, StringIO()
    try:
        command(*args, **kwargs)
        sys.stdout.seek(0)
        yield sys.stdout.read()
    finally:
        sys.stdout = out


class BaseResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.rf = RequestFactory()
        cls.br = BaseResource()
        return

    def test_wrap_list(self):

        rcds = [{'id': 1, 'name': 'one'},
                {'id': 2, 'name': 'two'}]
        d = self.br.wrap_list_response(rcds)
        self.assertIn('count', d, "'count' key missing")
        self.assertEqual(d['count'], 2, "should have correct count")

    def test_check_search_criteria(self):

        mdl = Identifier()
        flds = copy.deepcopy(mdl._meta.fields)
        for fld in flds:
            if fld.column == 'barcode':
                continue
            if fld.column == 'linked_code':
                continue
            fld.concrete = False
            break
        req = self.rf.get("/resource?barcode=1234&linked_code=5678&not_a=90")
        self.br.request = req
        rv = self.br.check_search_criteria(flds)
        self.assertIn('barcode', rv, "should have 'barcode' field")
        self.assertIn('linked_code', rv, "should have 'linked_code' field")
        self.assertNotIn('not_a', rv, "should not have 'not_a' field")

    def test_filter_record(self):

        p = {'barcode': ('CharField', '1000015')}
        r = Identifier(barcode='1000015')
        rv = self.br.filter_record(p, r)
        self.assertTrue(rv, "should be True")

        p = {'uploaded': ('DateField', 'ge:2000-01-01')}
        r = Picture(uploaded=date.today())
        rv = self.br.filter_record(p, r)
        self.assertTrue(rv, "should be True")

        p = {'uploaded': ('DateField', 'bt:2000-01-01,2099-12-31')}
        r = Picture(uploaded=date.today())
        rv = self.br.filter_record(p, r)
        self.assertTrue(rv, "should be True")

        p = {'price': ('DecimalField', 'le:29.99')}
        r = Price(price=Decimal(7.95))
        rv = self.br.filter_record(p, r)
        self.assertTrue(rv, "should be True")

        p = {'price': ('DecimalField', 'bt:4.95,29.99')}
        r = Price(price=Decimal(7.95))
        rv = self.br.filter_record(p, r)
        self.assertTrue(rv, "should be True")

        p = {'item': ('ForeignKey', 'None')}
        r = Picture()
        rv = self.br.filter_record(p, r)
        self.assertTrue(rv, "should be True")

        p = {'count': ('IntegerField', 'lt:5')}
        r = Receipt(count=3)
        rv = self.br.filter_record(p, r)
        self.assertTrue(rv, "should be True")

        p = {'count': ('IntegerField', 'bt:1,9')}
        r = Receipt(count=5)
        rv = self.br.filter_record(p, r)
        self.assertTrue(rv, "should be True")

    def test_compare_values(self):

        rv = self.br.compare_values("or", 1, 2)
        self.assertFalse(rv, "'or' is not a comparator")

        rv = self.br.compare_values("lt", 5, 25)
        self.assertTrue(rv, "5 is less than 25")

        rv = self.br.compare_values("le", 15, 15)
        self.assertTrue(rv, "15 is less-or-equal 15")

        rv = self.br.compare_values("gt", 25, 10)
        self.assertTrue(rv, "25 is greater than 10")

        rv = self.br.compare_values("ge", 15, 15)
        self.assertTrue(rv, "15 is greater-or-equal 15")

        rv = self.br.compare_values("bt", 2, 1, 3)
        self.assertTrue(rv, "2 is greater than 1 and less than 3")


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

        wqs = '{}?name=basket'.format(url)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 1, "should return one record")
        self.assertEqual(d['objects'][0]['barcode'], '1010', "should return 'Basket 1'")

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

        wqs = '{}?name=choice'.format(url)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 1, "should return one record")
        self.assertEqual(d['objects'][0]['id'], 1, "should return 'Choice Fabrics'")

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

        wqs = '{}?description=Emerald'.format(url)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 1, "should return one record")
        self.assertEqual(d['objects'][0]['barcode'], '1000002', "should return 'Emerald City'")

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
                'part_unit': 'By the Yard'
                }
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
        item['yardage'] = True
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
        item['out_of_stock'] = True
        change = json.dumps(item)
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")

        item['brand'] = 'Windham'
        change = json.dumps(item)
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")

        change = json.dumps({'label': 'Dritz'})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertNotIn('label', d, ";label' field should not be in record")

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


class ItemDataResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        cls.barcode = '1000002'
        cls.badID = '1000022'
        cls.item = Identifier.idents.create(barcode=cls.barcode)
        vendor = Supplier.objects.create(name='My supplier')
        invoice = Invoice.objects.create(vendor=vendor)
        cls.invc = invoice.id
        cls.badInvc = 55
        ItemTemplate.objects.create(description='Emerald City',
                                    identifier=cls.item)

    def test_detail(self):

        url = reverse('itemdata-detail', kwargs={'digitstring': 'trial'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('digitstring', d['errors'], "digitstring error missing")
        self.assertEqual(d['errors']['digitstring'], "Must be a string of digits")

        pk = '1001954'
        url = reverse('itemdata-detail', kwargs={'digitstring': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return one-keypair")
        d = json.loads(response.content)
        self.assertEqual(len(d), 1, "should contain only one field")
        self.assertIn('digitstring', d, "Should return digitstring")

        pk = '1000002'
        url = reverse('itemdata-detail', kwargs={'digitstring': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an item")
        d = json.loads(response.content)
        self.assertEqual(d['barcode'], pk, "Identifiers should match")

    def test_create(self):

        url = reverse('itemdata-list')
        response = self.client.post(url, {'name': 'bitmap'},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'description': ''},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('item', d['errors'], "item error missing")
        self.assertEqual(d['errors']['item'], "No item ID")

        response = self.client.post(url, {'item': self.badID},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('item', d['errors'], "item error missing")
        self.assertEqual(d['errors']['item'], "Item not found")

        response = self.client.post(url, {'item': self.barcode},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 201, "should return 'Created'")

        response = self.client.post(url, {'item': self.barcode,
                                          'units': 2, 'price': '7.99'},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('StockBook', d, "StockBook tag missing")

        response = self.client.post(url, {'item': self.barcode,
                                          'units': 2, 'cost': '7.99'},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertNotIn('StockBook', d, "StockBook tag found")

        response = self.client.post(url, {'item': self.barcode,
                                          'cost': '2.99'},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('invoice', d['errors'], "invoice error missing")
        self.assertEqual(d['errors']['invoice'], "No invoice ID")

        response = self.client.post(url, {'item': self.barcode,
                                          'cost': '2.99', 'invoice': self.badInvc},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('invoice', d['errors'], "invoice error missing")
        self.assertEqual(d['errors']['invoice'], "Invoice not found")

        response = self.client.post(url, {'item': self.barcode,
                                          'cost': '2.99', 'invoice': self.invc},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('purchase', d, "Purchase tag missing")

        response = self.client.post(url, {'item': self.barcode,
                                          'cost': '2.99', 'invoice': self.invc},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('purchase', d, "Purchase tag missing")

        response = self.client.post(url, {'item': self.barcode,
                                          'price': '7.99'},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('price', d, "Price tag missing")

        response = self.client.post(url, {'item': self.barcode,
                                          'price': '19.99'},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('price', d, "Price tag missing")


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
        cls.itmID2 = '1000028'
        ItemTemplate.objects.create(description='Small Bitmap',
                                    identifier=Identifier.idents.create(barcode=cls.itmID))
        itm = ItemTemplate.objects.create(description='Another Bitmap',
                                          identifier=Identifier.idents.create(barcode=cls.itmID2))
        cls.image_file = 'inventory/tests/data/small.bmp'
        Picture.objects.create(photo=cls.image_file)
        Picture.objects.create(photo=cls.image_file)
        Picture.objects.create(photo=cls.image_file, item=itm)

    def test_list(self):
        url = reverse('picture-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('photo', each, "should have photo field")

        wqs = '{}?item=None'.format(url)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 2, "should return two records")
        self.assertEqual(d['objects'][0]['item_id'], None, "should return unlinked records")

        wqs = '{0}?item={1}'.format(url, self.itmID2)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['objects'][0]['item_id'], self.itmID2, "should return linked record")

        now = date.today()
        datestr = now.strftime("%Y-%m-%d")
        wqs = '{0}?uploaded=le:{1}'.format(url, datestr)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 3, "should return three records")

        now += timedelta(days=2)
        datestr = now.strftime("%Y-%m-%d")
        wqs = '{0}?uploaded=eq:{1}'.format(url, datestr)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 0, "should return empty list")

    def test_detail(self):
        pk = 2
        url = reverse('picture-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a picture")
        d = json.loads(response.content)
        self.assertIn('photo', d, "key field missing")

    def test_create(self):
        url = reverse('picture-list')
        response = self.client.post(url, {'name': 'bitmap'},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'description': ''},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('photo', d['errors'], "photo error missing")
        self.assertEqual(d['errors']['photo'], "No file uploaded")

        with TemporaryDirectory() as tmpdirname:
            with self.settings(MEDIA_ROOT=tmpdirname):
                with open(self.image_file, 'rb') as fp:
                    response = self.client.post(url, {'photo': fp})
                    d = json.loads(response.content)

        self.assertEqual(response.status_code, 201, "should return 'Created'")
        d = json.loads(response.content)
        self.assertIn('photo', d, "should return filename")

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
        cls.locID2 = '1010'
        cls.itmID = '1000002'
        cls.itm2 = '1000015'
        cls.itm3 = '1000028'
        cls.itm4 = '1000031'
        l1 = Location.objects.create(
                    name='here',
                    identifier=Identifier.idents.create(barcode=cls.locID))
        l2 = Location.objects.create(
                    name='there',
                    identifier=Identifier.idents.create(barcode=cls.locID2))
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
        ItemTemplate.objects.create(
                    description='And one more',
                    yardage=False,
                    identifier=Identifier.idents.create(barcode=cls.itm4))
        StockBook.objects.create(itm=i1, loc=l1, units=1.25)
        StockBook.objects.create(itm=i2, loc=l2)

    def test_detail(self):
        url = reverse('stock-detail', kwargs={'pk': 1000})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('itm_id', d['errors'], "itm_id error missing")
        self.assertEqual(d['errors']['itm_id'], "Item not found")

        url = reverse('stock-detail', kwargs={'pk': self.itm3})
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

    def test_list(self):

        url = reverse('stock-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('created', each, "should have 'created' field")

        wqs = '{0}?loc={1}'.format(url, self.locID)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 1, "should return one record")
        self.assertEqual(d['objects'][0]['loc'], self.locID, "should return location")

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

        response = self.client.post(url, {'itm_id': self.itm3, 'loc_id': 'far'},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('loc_id', d['errors'], "loc_id error missing")
        self.assertEqual(d['errors']['loc_id'], "Location not found")

        response = self.client.post(url, {'itm_id': self.itm3,
                                          'loc_id': self.locID},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('created', d, "'created' field missing")

        response = self.client.post(url, {'itm_id': self.itm4, 'units': 4},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('units', d, "units field missing")

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

        response = self.client.put(url, '{"units": 42}')
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('created', d, "created timestamp missing")

        response = self.client.put(url, '{"units": 42, "loc_id": 1010}')
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('created', d, "created timestamp missing")


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
        cls.itm3 = '1000028'
        cls.itmNF = '1000090'
        cls.amount = 7.99
        cls.expensive = 24.99
        i1 = ItemTemplate.objects.create(
                    description='Bolt of Fabric',
                    identifier=Identifier.idents.create(barcode=cls.itmID))
        i2 = ItemTemplate.objects.create(
                    description='Fabric Panel',
                    yardage=False,
                    identifier=Identifier.idents.create(barcode=cls.itm2))
        i3 = ItemTemplate.objects.create(
                    description='Inventoried Item',
                    yardage=False,
                    identifier=Identifier.idents.create(barcode=cls.itm3))
        Price.objects.create(itm=i1, price=cls.expensive)
        Price.objects.create(itm=i2, price=cls.amount)
        return

    def test_detail(self):
        url = reverse('price-detail', kwargs={'pk': self.itmNF})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('itm_id', d['errors'], "itm_id error missing")
        self.assertEqual(d['errors']['itm_id'], "Item not found")

        url = reverse('price-detail', kwargs={'pk': self.itm3})
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
        self.assertEqual(d['price'], '{}'.format(self.expensive))

    def test_list(self):

        url = reverse('price-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('created', each, "should have 'created' field")

        wqs = '{0}?price=ge:{1}'.format(url, self.expensive)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 1, "should return one record")

    def test_create(self):
        url = reverse('price-list')
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

        response = self.client.post(url, {'itm_id': self.itmNF},
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

        response = self.client.post(url, {'itm_id': self.itm3,
                                          'price': self.amount},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('price', d, "price field missing")

    def test_update(self):

        url = reverse('price-detail', kwargs={'pk': self.itmNF})
        response = self.client.put(url, 'Invalid item ID')
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.put(url, '{"itm_id": 1000}')
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('itm_id', d['errors'], "itm_id error missing")
        self.assertEqual(d['errors']['itm_id'], "Item not found")

        url = reverse('price-detail', kwargs={'pk': self.itm3})
        change = json.dumps({'discount': 10})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('price', d, "price field missing")
        self.assertIsNone(d['price'], "price field set")

        url = reverse('price-detail', kwargs={'pk': self.itm3})
        amount = '0.99'
        change = json.dumps({'price': amount})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "errors container found")
        self.assertIn('price', d, "price field missing")
        self.assertEqual(d['price'], amount)


class InvoiceResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        cls.sup1 = Supplier.objects.create(name='Milltown')
        cls.sup2 = Supplier.objects.create(name='Bedoses Fabric')
        inv101 = Invoice.objects.create(id=101, vendor=cls.sup1)
        inv102 = Invoice.objects.create(id=102, vendor=cls.sup1)
        inv103 = Invoice.objects.create(id=103, vendor=cls.sup2)
        inv104 = Invoice.objects.create(id=104, vendor=cls.sup2)
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

    def test_list(self):

        url = reverse('invoice-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('received', each, "should have 'received' field")

        wqs = '{0}?vendor={1}'.format(url, self.sup1.id)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 2, "should return two records")
        self.assertEqual(d['objects'][0]['vendor'], self.sup1.id, "should return vendor")

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
        self.assertEqual(d['id'], 105)


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
        inv103 = Invoice.objects.create(id=103, vendor=sup2)
        itm2 = ItemTemplate.objects.create(
                    description='Emerald City',
                    identifier=Identifier.idents.create(barcode='1000002'))
        itm28 = ItemTemplate.objects.create(
                    description='Fields of Popae',
                    identifier=Identifier.idents.create(barcode='1000028'))
        cls.pchs = Purchase.objects.create(invoice=inv101, item=itm2)
        Purchase.objects.create(invoice=inv101, item=itm28)
        Purchase.objects.create(invoice=inv103, item=itm2)
        cls.inv1 = inv101
        cls.inv2 = inv102
        cls.itm28 = itm28

    def test_detail(self):

        url = reverse('purchase-detail', kwargs={'pk': 5})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('id', d['errors'], "id error missing")
        self.assertEqual(d['errors']['id'], "Purchase #5 not found")

        url = reverse('purchase-detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an order")
        d = json.loads(response.content)
        self.assertIn('invoice', d, "invoice id missing")
        self.assertEqual(d['invoice'], self.pchs.invoice_id)
        self.assertIn('item', d, "item id missing")
        self.assertEqual(d['item'], self.pchs.item_id)

    def test_list(self):

        url = reverse('purchase-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('cost', each, "should have 'cost' field")

        wqs = '{0}?invoice={1}'.format(url, self.inv1.id)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 2, "should return two records")
        self.assertEqual(d['objects'][0]['invoice'], self.inv1.id, "should return invoice")

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

    def test_update(self):

        url = reverse('purchase-detail', kwargs={'pk': 5})
        response = self.client.put(url, "Non-existent record")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        change = json.dumps({'cost': '19.95'})
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('id', d['errors'], "id error missing")
        self.assertEqual(d['errors']['id'], "Purchase #5 not found")

        url = reverse('purchase-detail', kwargs={'pk': 1})
        response = self.client.put(url, json.dumps({'item': 28}))
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertNotEqual(d['item'], 28, "item should not be changed")

        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertEqual(d['cost'], '19.95', "cost should be changed")

        response = self.client.put(url, json.dumps({'cost': '-10%'}))
        self.assertEqual(response.status_code, 202, "should return 'Accepted'")
        d = json.loads(response.content)
        self.assertEqual(d['cost'], '19.95', "cost should not be changed")

        return


class ReceiptResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        cls.r1 = Receipt.objects.create(id=1001, count=1, amount=7.99)
        cls.r2 = Receipt.objects.create(id=1002, count=1, amount=14.79)

    def test_detail(self):
        url = reverse('receipt-detail', kwargs={'pk': 5})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('id', d['errors'], "id error missing")
        self.assertEqual(d['errors']['id'], "Receipt #5 not found")

        url = reverse('receipt-detail', kwargs={'pk': self.r2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a receipt")
        d = json.loads(response.content)
        self.assertIn('id', d, "id field missing")
        self.assertEqual(d['id'], self.r2.id)
        self.assertIn('amount', d, "amount field missing")
        self.assertEqual(d['amount'], str(self.r2.amount))

    def test_list(self):
        url = reverse('receipt-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('created', each, "should have 'created' field")

        wqs = '{0}?amount=eq:{1}'.format(url, self.r1.amount)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 1, "should return one record")
        self.assertEqual(d['objects'][0]['amount'], str(self.r1.amount), "should return amount")

    def test_create(self):
        url = reverse('receipt-list')
        response = self.client.post(url, {}, content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {}, content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('id', d, "should have created a record")
        self.assertIn('status', d, "should have a default status")
        self.assertEqual(d['status'], "OPEN", " hould have status of 'Open'")

    def test_update(self):
        url = reverse('receipt-detail', kwargs={'pk': 1001})
        change = json.dumps({'status': 'AWK!'})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('status', d['errors'], "status error message missing")
        self.assertEqual(d['errors']['status'], "'AWK!' is not a valid status")

        change = json.dumps({'count': 5, 'amount': 24.79})
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "update should succeed")
        self.assertEqual(d['count'], 5, "count should be updated")
        self.assertEqual(d['amount'], 24.79, "amount should be updated")

        change = json.dumps({'status': 'CMPL'})
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "update should succeed")
        self.assertEqual(d['status'], 'CMPL', "status should be updated")


class ItemSaleResourceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           is_superuser=True,
                                           password='rubySlippers')
        cls.r1001 = Receipt.objects.create(id=1001, count=1, amount=7.99)
        id002 = Identifier.idents.create(barcode=1000002)
        id015 = Identifier.idents.create(barcode=1000015)
        cls.itm02 = ItemTemplate.objects.create(identifier_id=1000002,
                                                description="random yardage")
        cls.itm15 = ItemTemplate.objects.create(identifier_id=1000015,
                                                description="more yardage")
        cls.tran01 = ItemSale.objects.create(receipt=cls.r1001, item=cls.itm02,
                                             count=2, amount=7.98)
        cls.tran02 = ItemSale.objects.create(receipt=cls.r1001, item=cls.itm15,
                                             count=1, amount=3.99)
        return

    def test_detail(self):
        url = reverse('itemsale-detail', kwargs={'pk': 5})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an error")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container missing")
        self.assertIn('id', d['errors'], "id error missing")
        self.assertEqual(d['errors']['id'], "ItemSale #5 not found")

        url = reverse('itemsale-detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return an order")
        d = json.loads(response.content)
        self.assertIn('receipt', d, "receipt id missing")
        self.assertEqual(d['receipt'], self.tran01.receipt_id)
        self.assertIn('item', d, "item id missing")
        self.assertEqual(d['item'], str(self.tran01.item_id))

    def test_list(self):
        url = reverse('itemsale-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "should return a list")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        for each in d['objects']:
            self.assertIn('count', each, "should have 'count' field")

        wqs = '{0}?count=eq:{1}'.format(url, self.tran01.count)
        response = self.client.get(wqs)
        self.assertEqual(response.status_code, 200, "should return a list of one item")
        d = json.loads(response.content)
        self.assertIn('objects', d, "objects container missing")
        self.assertEqual(d['count'], 1, "should return one record")
        self.assertEqual(d['objects'][0]['id'], self.tran01.id, "should return record 1")
        self.assertEqual(d['objects'][0]['count'], self.tran01.count, "should return count")

    def test_create(self):
        url = reverse('itemsale-list')
        response = self.client.post(url, {}, content_type="application/json")
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.post(url, {'receipt_id': 111},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container is missing")
        self.assertIn('receipt_id', d['errors'], "receipt message is missing")
        self.assertEqual(d['errors']['receipt_id'],
                         "Receipt #111 not found", "wrong receipt message")
        self.assertIn('item_id', d['errors'], "item message is missing")
        self.assertEqual(d['errors']['item_id'], "An item is required", "wrong item message")

        response = self.client.post(url, {'item_id': 111},
                                    content_type="application/json")
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container is missing")
        self.assertIn('receipt_id', d['errors'], "receipt message is missing")
        self.assertEqual(d['errors']['receipt_id'],
                         "A receipt is required", "wrong receipt message")
        self.assertIn('item_id', d['errors'], "item message is missing")
        self.assertEqual(d['errors']['item_id'], "Item 111 not found", "wrong item message")

        data = {'receipt_id': 1001, 'item_id': 1000002, 'count': 1, 'amount': 3.99}
        response = self.client.post(url, data, content_type="application/json")
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "create should succeed")
        self.assertIn('id', d, "create should assign an id")

    def test_update(self):
        url = reverse('itemsale-detail', kwargs={'pk': 11})
        change = json.dumps({'adjusted': ''})
        response = self.client.put(url, change)
        self.assertEqual(response.status_code, 401, "should return 'Unauthorized'")

        self.client.login(username='dorothy', password='rubySlippers')
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertIn('errors', d, "errors container is missing")
        self.assertIn('id', d['errors'], "error message is missing")
        self.assertEqual(d['errors']['id'], "ItemSale #11 not found", "wrong error message")

        url = reverse('itemsale-detail', kwargs={'pk': 1})
        change = json.dumps({'receipt_id': 1001, 'item_id': '1000015'})
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "update should succeed")
        self.assertEqual(d['item'], '1000015', "item should be updated")

        change = json.dumps({'adjusted': 7.99})
        response = self.client.put(url, change)
        d = json.loads(response.content)
        self.assertNotIn('errors', d, "update should succeed")
        self.assertEqual(d['adjusted'], 7.99, "adjustment should be updated")
