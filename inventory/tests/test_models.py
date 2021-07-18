from django.test import TestCase

from ..models import Identifier


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
        self.assertEquals(result, '1007')
        Identifier.idents.create(barcode='1007')
        result = Identifier.make_loc_id()
        self.assertEquals(result, '1010')

    def test_make_itemID(self):
        result = Identifier.make_item_id()
        self.assertEquals(result, '1000002')
        Identifier.idents.create(barcode='1000002')
        result = Identifier.make_item_id()
        self.assertEquals(result, '1000015')

    def test_get_absolute_url(self):
        id = Identifier(barcode='123')
        result = id.get_absolute_url()
        self.assertEquals(result, '/inventory/identifier/123')
