import decimal
import json
import sys
from datetime import date
from decimal import Decimal

from restless.data import Data
from restless.preparers import FieldsPreparer

from .dj4 import DjangoResource
from .models import Identifier, Location, Supplier, ItemTemplate, Picture
from .models import StockBook, Price, Invoice, Purchase


class BaseResource(DjangoResource):

    def wrap_list_response(self, data):

        d = super(BaseResource, self).wrap_list_response(data)
        d['count'] = len(d['objects'])

        return d

    def deserialize_list(self, body):
        """
        Given a string of text, deserializes a (presumed) list out of the body.

        :param body: The body of the current request
        :type body: string

        :returns: The deserialized body or an empty ``list``
        """
        rv = []
        bbod = b'' if body == '' else body
        if self.request.content_type == 'multipart/form-data':
            bbod = b''
        if bbod:
            rv = self.serializer.deserialize(bbod)
        #
        return rv

    def check_search_criteria(self, fld_set):
        params = {}
        for ix in range(len(fld_set)):
            fld_desc = fld_set[ix]
            # only search on 'real' columns
            if not getattr(fld_desc, 'concrete'):
                continue
            nm = getattr(fld_desc, 'name', None)
            if nm not in self.request.GET:
                continue
            typ = fld_desc.get_internal_type()
            val = self.request.GET[nm]
            params[nm] = (typ, val)
        return params

    def filter_record(self, params, record):
        keep = True
        for k, v in params.items():
            typ = v[0]
            val = v[1]
            fld = getattr(record, k, None)
            # TODO:  replace with 'match-case' construct
            if typ == 'CharField' or typ == 'TextField':
                if not val.lower() in fld.lower():
                    keep = False
            elif typ == 'ForeignKey' or typ == 'OneToOneField':
                key = getattr(record, '{}_id'.format(k), None)
                if val == 'None':   # looking for unlinked records
                    keep = True if fld is None else False
                else:   # looking for a specific link
                    keep = True if (val == key or int(val) == key) else False
            else:
                d2 = None
                [cmp, info] = val.split(':')
                d1 = info
                if cmp == 'bt':
                    [d1, d2] = info.split(',')
                if typ == 'DateField':
                    limit = date.fromisoformat(d2) if d2 else None
                    when = date.fromisoformat(d1)
                    keep = self.compare_values(cmp, fld, when, limit)
                elif typ == 'DecimalField':
                    limit = Decimal(d2) if d2 else None
                    amount = Decimal(d1)
                    keep = self.compare_values(cmp, fld, amount, limit)
                else:   # default to numeric values
                    limit = int(d2) if d2 else None
                    number = int(d1)
                    keep = self.compare_values(cmp, fld, number, limit)
            # end of 'match-case' construct
            if not keep:
                break
        return keep

    def compare_values(self, typ, val0, val1, val2=None):
        rv = False

        if typ == 'bt':     # between
            rv = val0 > val1 and val0 < val2
        elif typ == 'eq':   # equal
            rv = val0 == val1
        elif typ == 'ge':   # greater or equal
            rv = val0 >= val1
        elif typ == 'gt':   # greater than
            rv = val0 > val1
        elif typ == 'le':   # less or equal
            rv = val0 <= val1
        elif typ == 'lt':   # less than
            rv = val0 < val1
        #
        return rv


class IdentResource(BaseResource):

    def is_authenticated(self):
        if self.request.method == 'GET':
            return True
        else:
            return False

    # GET /api/idents/<digitstring>
    def detail(self, digitstring):

        data = {'digitstring': digitstring}
        if not digitstring.isdigit():
            errs = {'digitstring': 'Must be a string of digits'}
            return Data({'errors': errs}, should_prepare=False)

        try:
            id = Identifier.idents.get(barcode=digitstring)
        except Identifier.DoesNotExist:
            try:
                id = Identifier.idents.get(linked_code=digitstring)
            except Identifier.DoesNotExist:
                id = None

        ident = id.barcode if id else ""
        data['identifier'] = ident
        data['type'] = 'OTHER'
        if len(ident) == Identifier.LOC_LEN:
            data['type'] = 'LOC'
        if len(ident) == Identifier.ITM_LEN:
            data['type'] = 'ITM'
        return data


class LocIdResource(BaseResource):
    preparer = FieldsPreparer(fields={
        'barcode': 'barcode',
    })

    def is_authenticated(self):
        if self.request.method == 'GET':
            return True
        user = self.request.user
        ok = user.has_perm('inventory.add_identifier')
        return ok

    # GET /api/locid/
    def list(self):
        qs = Identifier.locIDs.all()
        return qs

    # GET /api/locid/<pk>/
    def detail(self, pk):
        qs = Identifier.locIDs.get(barcode=pk)
        return qs

    # POST /api/locid/
    def create(self):
        bc = Identifier.make_loc_id()
        id = Identifier.locIDs.create(barcode=bc)
        return id


class LocationResource(BaseResource):
    preparer = FieldsPreparer(fields={
        'name': 'name',
        'description': 'description',
        'locID': 'identifier.urlize',
        'barcode': 'identifier_id'
    })

    def __init__(self, *args, **kwargs):
        super(LocationResource, self).__init__(*args, **kwargs)

        self.http_methods['detail'].update({
                'PATCH': 'print_label',
        })
        return

    def is_authenticated(self):
        if self.request.method in {'GET', 'PATCH'}:
            return True
        user = self.request.user
        ok = user.has_perm('inventory.add_location')
        return ok

    # GET /api/location/
    def list(self):
        qs = Location.objects.all()
        # check for search parameters
        params = self.check_search_criteria(Location._meta.fields)
        if params:
            rcds = []
            for rcd in qs.iterator():
                keep = self.filter_record(params, rcd)
                if keep:
                    rcds.append(rcd)
            return rcds
        # no filters; just return everything
        return qs

    # GET /api/location/<pk>/
    def detail(self, pk):
        qs = Location.objects.get(identifier_id=pk)
        return qs

    # POST /api/location/
    def create(self):

        errs = {}
        name = self.data['name'] if 'name' in self.data else None
        if not name:
            errs = {'name': 'A name is required'}
        else:
            found = Location.objects.filter(name=name).exists()
            if found:
                errs = {'name': 'Name already used -- pick another'}
        if errs:
            return Data({'errors': errs}, should_prepare=False)

        loc = Location()
        for fld in ['name', 'description']:
            val = self.data[fld] if fld in self.data else None
            setattr(loc, fld, val)

        bc = Identifier.make_loc_id()
        id = Identifier.locIDs.create(barcode=bc)
        setattr(loc, 'identifier', id)

        loc.save()
        return loc

    # PUT /api/location/<pk>/
    def update(self, pk):

        loc = Location.objects.get(identifier_id=pk)
        name = self.data['name'] if 'name' in self.data else loc.name
        if name != loc.name:
            found = Location.objects.filter(name=name).exists()
            if found:
                errs = {'name': 'Name already used -- pick another'}
                return Data({'errors': errs}, should_prepare=False)

        for fld in ['name', 'description']:
            val = self.data[fld] if fld in self.data else None
            if val is not None:
                setattr(loc, fld, val)

        loc.save()
        return loc

    def print_label(self, pk):

        loc = Location.objects.get(identifier_id=pk)
        print('Printing barcode label for Location "{}"'.format(loc))
        return


class SupplierResource(BaseResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'name': 'name',
        'street': 'street',
        'street_ext': 'street_ext',
        'city': 'city',
        'state': 'state',
        'zip5': 'zip5',
        'phone_1': 'phone_1',
        'phone_2': 'phone_2',
        'notes': 'notes'
    })

    def is_authenticated(self):
        if self.request.method == 'GET':
            return True
        user = self.request.user
        ok = user.has_perm('inventory.add_supplier')
        return ok

    # GET /api/supplier/
    def list(self):
        qs = Supplier.objects.all()
        # check for search parameters
        params = self.check_search_criteria(Supplier._meta.fields)
        if params:
            rcds = []
            for rcd in qs.iterator():
                keep = self.filter_record(params, rcd)
                if keep:
                    rcds.append(rcd)
            return rcds
        # no filters; just return everything
        return qs

    # GET /api/supplier/<pk>/
    def detail(self, pk):
        qs = Supplier.objects.get(id=pk)
        return qs

    # POST /api/supplier/
    def create(self):

        errs = {}
        name = self.data['name'] if 'name' in self.data else None
        if not name:
            errs = {'name': 'A name is required'}
        else:
            found = Supplier.objects.filter(name=name).exists()
            if found:
                errs = {'name': 'Name already used -- pick another'}
        if errs:
            return Data({'errors': errs}, should_prepare=False)

        who = Supplier()
        for fld in ['name', 'street', 'street_ext', 'city', 'state', 'zip5',
                    'phone_1', 'phone_2', 'notes']:
            val = self.data[fld] if fld in self.data else None
            setattr(who, fld, val)

        who.save()
        return who

    # PUT /api/supplier/<pk>/
    def update(self, pk):

        who = Supplier.objects.get(id=pk)
        name = self.data['name'] if 'name' in self.data else who.name
        if name != who.name:
            found = Supplier.objects.filter(name=name).exists()
            if found:
                errs = {'name': 'Name already used -- pick another'}
                return Data({'errors': errs}, should_prepare=False)

        for fld in ['name', 'street', 'street_ext', 'city', 'state', 'zip5',
                    'phone_1', 'phone_2', 'notes']:
            val = self.data[fld] if fld in self.data else None
            if val is not None:
                setattr(who, fld, val)

        who.save()
        return who


class ItemTemplateResource(BaseResource):
    preparer = FieldsPreparer(fields={
        'description': 'description',
        'brand': 'brand',
        'content': 'content',
        'part_unit': 'part_unit',
        'yardage': 'yardage',
        'notes': 'notes',
        'itmID': 'identifier.urlize',
        'barcode': 'identifier_id',
        'linked_code': 'identifier.linked_code'
    })

    def __init__(self, *args, **kwargs):
        super(ItemTemplateResource, self).__init__(*args, **kwargs)

        self.http_methods['detail'].update({
                'PATCH': 'print_label',
        })
        return

    def is_authenticated(self):
        if self.request.method in {'GET', 'PATCH'}:
            return True
        user = self.request.user
        ok = user.has_perm('inventory.add_itemtemplate')
        return ok

    # GET /api/item/
    def list(self):
        qs = ItemTemplate.objects.all()
        # check for search parameters
        params = self.check_search_criteria(ItemTemplate._meta.fields)
        if params:
            rcds = []
            for rcd in qs.iterator():
                keep = self.filter_record(params, rcd)
                if keep:
                    rcds.append(rcd)
            return rcds
        # no filters; just return everything
        return qs

    # GET /api/item/<pk>/
    def detail(self, pk):
        qs = ItemTemplate.objects.get(identifier_id=pk)
        return qs

    # POST /api/item/
    def create(self):

        errs = {}
        desc = self.data['description'] if 'description' in self.data else None
        if not desc:
            errs = {'description': 'A description is required'}
        else:
            found = ItemTemplate.objects.filter(description=desc).exists()
            if found:
                errs = {'description': 'Description already used -- pick another'}
        if errs:
            return Data({'errors': errs}, should_prepare=False)

        item = ItemTemplate()
        for fld in ['description', 'brand', 'content', 'part_unit', 'notes']:
            val = self.data[fld] if fld in self.data else None
            setattr(item, fld, val)

        for fld in ['yardage']:
            tf = self.data[fld] if fld in self.data else None
            if tf is not None:
                setattr(item, fld, tf)

        upc = self.data['linked_code'] if 'linked_code' in self.data else ''
        bc = Identifier.make_item_id()
        id = Identifier.itemIDs.create(barcode=bc)
        if upc:
            setattr(id, 'linked_code', upc)
            id.save()
        setattr(item, 'identifier', id)

        item.save()
        return item

    # PUT /api/item/<pk>/
    def update(self, pk):

        upc = self.data['linked_code'] if 'linked_code' in self.data else ''
        if upc:
            bc = Identifier.itemIDs.get(barcode=pk)
            if not bc.linked_code == upc:
                setattr(bc, 'linked_code', upc)
                bc.save()

        item = ItemTemplate.objects.get(identifier_id=pk)
        desc = self.data['description'] if 'description' in self.data else item.description
        if desc != item.description:
            found = ItemTemplate.objects.filter(description=desc).exists()
            if found:
                errs = {'description': 'Description already used -- pick another'}
                return Data({'errors': errs}, should_prepare=False)

        changes = False
        for fld in ['description', 'brand', 'content', 'part_unit', 'notes']:
            val = self.data[fld] if fld in self.data else None
            if val is not None:
                setattr(item, fld, val)
                changes = True

        for fld in ['yardage', 'out_of_stock']:
            tf = self.data[fld] if fld in self.data else None
            if tf is not None:
                setattr(item, fld, tf)
                changes = True

        if changes:
            item.save()
        return item

    def print_label(self, pk):

        item = ItemTemplate.objects.get(identifier_id=pk)
        print('Printing barcode label for Item "{}"'.format(item))
        return


class ItemDataResource(BaseResource):

    def is_authenticated(self):
        if self.request.method == 'GET':
            return True
        user = self.request.user
        ok = user.has_perm('inventory.add_purchase')
        return ok

    # GET /api/itemdata/<digitstring>
    def detail(self, digitstring):

        data = {'digitstring': digitstring}
        if not digitstring.isdigit():
            errs = {'digitstring': 'Must be a string of digits'}
            return Data({'errors': errs}, should_prepare=False)

        try:
            ident = Identifier.idents.get(barcode=digitstring)
        except Identifier.DoesNotExist:
            try:
                ident = Identifier.idents.get(linked_code=digitstring)
            except Identifier.DoesNotExist:
                ident = None

        if ident:
            data['barcode'] = ident.barcode
            data['linked_code'] = ident.linked_code
            data['itmID'] = ident.urlize()
            item = ItemTemplate.objects.get(identifier_id=ident.barcode)
            for fld in ['description', 'brand', 'content', 'part_unit', 'yardage', 'notes']:
                val = getattr(item, fld, None)
                if val:
                    data[fld] = val

        return data

    # POST /api/itemdata
    def create(self):

        updates = {}
        itm_id = self.data['item'] if 'item' in self.data else None
        if not itm_id:
            errs = {'item': 'No item ID'}
            return Data({'errors': errs}, should_prepare=False)

        try:
            item = ItemTemplate.objects.get(identifier_id=itm_id)
        except ItemTemplate.DoesNotExist:
            errs = {'item': 'Item not found'}
            return Data({'errors': errs}, should_prepare=False)

        # update StockBook record
        if 'units' in self.data or 'eighths' in self.data:
            units = self.data['units'] if 'units' in self.data else None
            eighths = self.data['eighths'] if 'eighths' in self.data else None
            stockRcd, created = StockBook.objects.get_or_create(itm=item)
            if units and stockRcd.units != int(units):
                setattr(stockRcd, 'units', units)
                created = True
            if eighths and stockRcd.eighths != int(eighths):
                setattr(stockRcd, 'eighths', eighths)
                created = True
            if created:
                stockRcd.save()
            updates['StockBook'] = created

        # update Purchase record
        if 'cost' in self.data:
            money = Decimal( self.data['cost'] )
            inv_id = self.data['invoice'] if 'invoice' in self.data else None
            if not inv_id:
                errs = {'invoice': 'No invoice ID'}
                return Data({'errors': errs}, should_prepare=False)
            try:
                invoice = Invoice.objects.get(id=inv_id)
            except Invoice.DoesNotExist:
                errs = {'invoice': 'Invoice not found'}
                return Data({'errors': errs}, should_prepare=False)

            purchase, created = Purchase.objects.get_or_create(invoice=invoice, item=item)
            if not created:
                money += purchase.cost
            setattr( purchase, 'cost', money )
            purchase.save()
            updates['purchase'] = purchase.id

        # update Price record
        if 'price' in self.data:
            money = Decimal( self.data['price'] )
            try:
                priceRcd = Price.objects.filter(itm=item).latest('updated')
            except Price.DoesNotExist:
                priceRcd = Price(itm=item)
            if money != priceRcd.price:
                setattr(priceRcd, 'price', money)
                priceRcd.save()
            updates['price'] = priceRcd.price

        return updates


class PictureResource(BaseResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'photo': 'photo.name',
        'uploaded': 'uploaded',
        'item_id': 'item_id',
    })

    def is_authenticated(self):
        if self.request.method == 'GET':
            return True
        user = self.request.user
        ok = user.has_perm('inventory.add_picture')
        return ok

    # GET /api/picture/
    def list(self):
        qs = Picture.objects.all()
        # check for search parameters
        params = self.check_search_criteria(Picture._meta.fields)
        if params:
            rcds = []
            for rcd in qs.iterator():
                keep = self.filter_record(params, rcd)
                if keep:
                    rcds.append(rcd)
            return rcds
        # no filters; just return everything
        return qs

    # GET /api/picture/<pk>/
    def detail(self, pk):
        qs = Picture.objects.get(id=pk)
        return qs

    # POST /api/picture/
    def create(self):
        image_file = None
        for fil in self.request.FILES:
            image_file = self.request.FILES[fil]

        if image_file is None:
            errs = {'photo': 'No file uploaded'}
            return Data({'errors': errs}, should_prepare=False)

        one = Picture(photo=image_file)
        one.save()
        return one

    # PUT /api/location/<pk>/
    def update(self, pk):

        img = Picture.objects.get(id=pk)
        fld = 'item_id'
        val = self.data[fld] if fld in self.data else None
        if val is None:
            errs = {'item_id': 'No identifier received'}
            return Data({'errors': errs}, should_prepare=False)

        if val:
            found = Identifier.itemIDs.filter(barcode=val).exists()
            if not found:
                errs = {'item_id': 'Not a valid identifier'}
                return Data({'errors': errs}, should_prepare=False)

        setattr(img, fld, val)
        img.save()
        return img


class StockBookResource(BaseResource):
    preparer = FieldsPreparer(fields={
        'itm': 'itm_id',
        'loc': 'loc_id',
        'units': 'units',
        'eighths': 'eighths',
        'created': 'created',
        'updated': 'updated',
    })

    def is_authenticated(self):
        if self.request.method == 'GET':
            return True
        user = self.request.user
        ok = user.has_perm('inventory.add_stockbook')
        return ok

    # GET /api/stockbook/
    def list(self):
        qs = StockBook.objects.all()
        # check for search parameters
        params = self.check_search_criteria(StockBook._meta.fields)
        if params:
            rcds = []
            for rcd in qs.iterator():
                keep = self.filter_record(params, rcd)
                if keep:
                    rcds.append(rcd)
            return rcds
        # no filters; just return everything
        return qs

    # GET /api/stockbook/<pk>/
    def detail(self, pk):
        try:
            item = ItemTemplate.objects.get(identifier_id=pk)
        except ItemTemplate.DoesNotExist:
            errs = {'itm_id': 'Item not found'}
            return Data({'errors': errs}, should_prepare=False)

        try:
            rcd = StockBook.objects.get(itm=item)
        except StockBook.DoesNotExist:
            errs = {'item': 'Record not found'}
            return Data({'errors': errs}, should_prepare=False)

        return rcd

    # POST /api/stockbook/
    def create(self):
        fld = 'itm_id'
        val = self.data[fld] if fld in self.data else None
        if not val:
            errs = {'itm_id': 'No item ID received'}
            return Data({'errors': errs}, should_prepare=False)

        try:
            item = ItemTemplate.objects.get(identifier_id=val)
        except ItemTemplate.DoesNotExist:
            errs = {'itm_id': 'Item not found'}
            return Data({'errors': errs}, should_prepare=False)

        found = True
        try:
            StockBook.objects.get(itm_id=val)
        except StockBook.DoesNotExist:
            found = False
        if found:
            errs = {'itm_id': 'Record already exists'}
            return Data({'errors': errs}, should_prepare=False)

        fld = 'loc_id'
        val = self.data[fld] if fld in self.data else None
        loc = None
        if val:
            try:
                loc = Location.objects.get(identifier_id=val)
            except Location.DoesNotExist:
                errs = {'loc_id': 'Location not found'}
                return Data({'errors': errs}, should_prepare=False)

        rcd = StockBook(itm=item, loc=loc)

        fld = 'eighths'
        val = self.data[fld] if fld in self.data else None
        eighths = val if item.yardage else None

        fld = 'units'
        units = self.data[fld] if fld in self.data else None

        if units:
            rcd.units = units
            rcd.eighths = eighths

        rcd.save()
        return rcd

    # PUT /api/stockbook/<pk>
    def update(self, pk):
        try:
            item = ItemTemplate.objects.get(identifier_id=pk)
        except ItemTemplate.DoesNotExist:
            errs = {'itm_id': 'Item not found'}
            return Data({'errors': errs}, should_prepare=False)

        loc = None
        fld = 'loc_id'
        val = self.data[fld] if fld in self.data else None
        if val:
            try:
                loc = Location.objects.get(identifier_id=val)
            except Location.DoesNotExist:
                errs = {'loc_id': 'Location not found'}
                return Data({'errors': errs}, should_prepare=False)

        qs = StockBook.objects.get_or_create(itm=item)
        rcd = qs[0]
        rcd.loc = loc if loc else rcd.loc

        fld = 'eighths'
        val = self.data[fld] if fld in self.data else None
        eighths = val if item.yardage else None

        fld = 'units'
        units = self.data[fld] if fld in self.data else None

        if units:
            rcd.units = units
            rcd.eighths = eighths

        rcd.save()
        return rcd


class PriceResource(BaseResource):
    preparer = FieldsPreparer(fields={
        'itm': 'itm_id',
        'price': 'price',
        'created': 'created',
        'updated': 'updated',
    })

    def is_authenticated(self):

        if self.request.method == 'GET':
            return True
        user = self.request.user
        ok = user.has_perm('inventory.add_price')
        return ok

    # GET /api/price/<pk>/
    def detail(self, pk):

        try:
            item = ItemTemplate.objects.get(identifier_id=pk)
        except ItemTemplate.DoesNotExist:
            errs = {'itm_id': 'Item not found'}
            return Data({'errors': errs}, should_prepare=False)

        try:
            rcd = Price.objects.get(itm=item)
        except Price.DoesNotExist:
            errs = {'item': 'Record not found'}
            return Data({'errors': errs}, should_prepare=False)

        return rcd

    # GET /api/price/
    def list(self):
        qs = Price.objects.all()
        # check for search parameters
        params = self.check_search_criteria(Price._meta.fields)
        if params:
            rcds = []
            for rcd in qs.iterator():
                keep = self.filter_record(params, rcd)
                if keep:
                    rcds.append(rcd)
            return rcds
        # no filters; just return everything
        return qs

    # POST /api/price/
    def create(self):
        fld = 'itm_id'
        val = self.data[fld] if fld in self.data else None
        if not val:
            errs = {'itm_id': 'No item ID received'}
            return Data({'errors': errs}, should_prepare=False)

        try:
            item = ItemTemplate.objects.get(identifier_id=val)
        except ItemTemplate.DoesNotExist:
            errs = {'itm_id': 'Item not found'}
            return Data({'errors': errs}, should_prepare=False)

        found = True
        try:
            Price.objects.get(itm_id=val)
        except Price.DoesNotExist:
            found = False
        if found:
            errs = {'itm_id': 'Record already exists'}
            return Data({'errors': errs}, should_prepare=False)

        rcd = Price(itm=item)

        fld = 'price'
        val = self.data[fld] if fld in self.data else None
        rcd.price = val

        rcd.save()
        return rcd

    # PUT /api/price/<pk>/
    def update(self, pk):

        try:
            item = ItemTemplate.objects.get(identifier_id=pk)
        except ItemTemplate.DoesNotExist:
            errs = {'itm_id': 'Item not found'}
            return Data({'errors': errs}, should_prepare=False)

        qs = Price.objects.get_or_create(itm=item)
        rcd = qs[0]

        fld = 'price'
        price = self.data[fld] if fld in self.data else None

        if price:
            rcd.price = price

        rcd.save()
        return rcd


class InvoiceResource(BaseResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'vendor': 'vendor_id',
        'received': 'received'
    })

    def is_authenticated(self):
        if self.request.method == 'GET':
            return True
        user = self.request.user
        ok = user.has_perm('inventory.add_invoice')
        return ok

    # GET /api/invoice/<pk>/
    def detail(self, pk):

        try:
            inv = Invoice.objects.get(id=pk)
        except Invoice.DoesNotExist:
            errs = {'id': 'Invoice #{} not found'.format(pk)}
            return Data({'errors': errs}, should_prepare=False)

        return inv

    # GET /api/invoice/
    def list(self):
        qs = Invoice.objects.all()
        # check for search parameters
        params = self.check_search_criteria(Invoice._meta.fields)
        if params:
            rcds = []
            for rcd in qs.iterator():
                keep = self.filter_record(params, rcd)
                if keep:
                    rcds.append(rcd)
            return rcds
        # no filters; just return everything
        return qs

    # POST /api/invoice/
    def create(self):

        errs = {}
        v_id = self.data['vendor_id'] if 'vendor_id' in self.data else None
        if v_id:
            try:
                vendor = Supplier.objects.get(id=v_id)
            except Supplier.DoesNotExist:
                errs = {'vendor_id': 'Supplier not found'}
        else:
            errs = {'vendor_id': 'A supplier is required'}

        if errs:
            return Data({'errors': errs}, should_prepare=False)

        inv = Invoice(vendor=vendor)
        inv.save()
        return inv

    # PUT /api/invoice/<pk>
    # def update(self, pk):
    #   no updatable fields


class PurchaseResource(BaseResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'invoice': 'invoice_id',
        'item': 'item_id',
        'cost': 'cost'
    })

    def is_authenticated(self):

        if self.request.method == 'GET':
            return True
        user = self.request.user
        ok = user.has_perm('inventory.add_purchase')
        return ok

    # GET /api/purchase/<pk>/
    def detail(self, pk):

        try:
            inv = Purchase.objects.get(id=pk)
        except Purchase.DoesNotExist:
            errs = {'id': 'Purchase #{} not found'.format(pk)}
            return Data({'errors': errs}, should_prepare=False)

        return inv

    # GET /api/purchase/
    def list(self):
        qs = Purchase.objects.all()
        # check for search parameters
        params = self.check_search_criteria(Purchase._meta.fields)
        if params:
            rcds = []
            for rcd in qs.iterator():
                keep = self.filter_record(params, rcd)
                if keep:
                    rcds.append(rcd)
            return rcds
        # no filters; just return everything
        return qs

    # POST /api/purchase/
    def create(self):

        errs = {}
        inv_id = self.data['invoice_id'] if 'invoice_id' in self.data else None
        if inv_id:
            try:
                vendor = Invoice.objects.get(id=inv_id)
            except Invoice.DoesNotExist:
                errs['invoice_id'] = 'Invoice #{} not found'.format(inv_id)
        else:
            errs['invoice_id'] = 'An invoice is required'

        itm_id = self.data['item_id'] if 'item_id' in self.data else None
        if itm_id:
            try:
                item = ItemTemplate.objects.get(identifier_id=itm_id)
            except ItemTemplate.DoesNotExist:
                errs['item_id'] = 'Item {} not found'.format(itm_id)
        else:
            errs['item_id'] = 'An item is required'

        if errs:
            return Data({'errors': errs}, should_prepare=False)

        try:
            pchs = Purchase.objects.get(invoice=vendor, item=item)
        except Purchase.DoesNotExist:
            pchs = Purchase(invoice=vendor, item=item)

        val = self.data['cost'] if 'cost' in self.data else None
        if val:
            try:
                cash = decimal.Decimal(val)
            except decimal.DecimalException:
                val = None
        if val:
            pchs.cost = cash

        pchs.save()
        return pchs

    # PUT /api/purchase/<pk>/
    def update(self, pk):

        try:
            pchs = Purchase.objects.get(id=pk)
        except Purchase.DoesNotExist:
            errs = {'id': 'Purchase #{} not found'.format(pk)}
            return Data({'errors': errs}, should_prepare=False)

        val = self.data['cost'] if 'cost' in self.data else None
        if val:
            try:
                cash = decimal.Decimal(val)
            except decimal.DecimalException:
                val = None
        if val:
            pchs.cost = cash

        pchs.save()
        return pchs
