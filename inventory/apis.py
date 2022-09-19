import json
import sys

from restless.data import Data
from restless.preparers import FieldsPreparer

from .dj4 import DjangoResource
from .models import Identifier, Location, Supplier, ItemTemplate, Picture


class BaseResource(DjangoResource):

    def wrap_list_response(self, data):

        d = super(BaseResource, self).wrap_list_response(data)
        d['count'] = len(d['objects'])

        return d


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
        for fld in ['description', 'brand', 'content',
                    'part_unit', 'yardage', 'notes']:
            val = self.data[fld] if fld in self.data else None
            setattr(item, fld, val)

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

        for fld in ['description', 'brand', 'content',
                    'part_unit', 'yardage', 'notes']:
            val = self.data[fld] if fld in self.data else None
            if val is not None:
                setattr(item, fld, val)

        item.save()
        return item

    def print_label(self, pk):

        item = ItemTemplate.objects.get(identifier_id=pk)
        print('Printing barcode label for Item "{}"'.format(item))
        return


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
        return qs

    # GET /api/picture/<pk>/
    def detail(self, pk):
        qs = Picture.objects.get(id=pk)
        return qs

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
