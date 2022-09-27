from django.test import TestCase

from ..models import Identifier, Location, Supplier, ItemTemplate, Picture
from ..models import StockBook


class IdentifierTest(TestCase):

    def test_name(self):
        ct = Identifier.idents.count()
        if ct > 0:
            item = Identifier.idents.first()
        else:
            item = Identifier(barcode='barcode')

        lbl = '{}'.format(item)
        self.assertEqual(lbl, item.barcode)

    def test_make_locID(self):
        result = Identifier.make_loc_id()
        self.assertEqual(result, '1007')
        Identifier.idents.create(barcode='1007')
        result = Identifier.make_loc_id()
        self.assertEqual(result, '1010')

    def test_make_itemID(self):
        result = Identifier.make_item_id()
        self.assertEqual(result, '1000002')
        Identifier.idents.create(barcode='1000002')
        result = Identifier.make_item_id()
        self.assertEqual(result, '1000015')


class LocationTest(TestCase):

    def test_name(self):
        name = 'Top Shelf'
        loc = Location(name=name)
        lbl = '{}'.format(loc)
        self.assertEqual(lbl, name)


class SupplierTest(TestCase):

    def test_name(self):
        name = "Four-Dollar Fabric"
        who = Supplier(name=name)
        lbl = '{}'.format(who)
        self.assertEqual(lbl, name)


class ItemTemplateTest(TestCase):

    def test_name(self):
        desc = 'Apple A Day Cotton Fabric'
        itm = ItemTemplate(description=desc)
        lbl = '{}'.format(itm)
        self.assertEqual(lbl, itm.description)


class PictureTest(TestCase):

    def test_name(self):
        pic = Picture(id=1)
        lbl = '{}'.format(pic)
        self.assertEqual(lbl, "Photo 1")


class StockBookTest(TestCase):

    def test_name(self):
        rcd = StockBook(itm_id=1000002,loc_id=1007)
        lbl = '{}'.format(rcd)
        self.assertEqual(lbl, "Stock Record for Item 1000002")
