import json
import sys

from restless.dj import DjangoResource
from restless.preparers import FieldsPreparer

from .models import Identifier, Location, Supplier


class BaseResource(DjangoResource):

    def wrap_list_response(self, data):

        d = super(BaseResource, self).wrap_list_response(data)
        d['count'] = len(d['objects'])

        return d


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

        for fld in ['name', 'street', 'street_ext', 'city', 'state', 'zip5',
                    'phone_1', 'phone_2', 'notes']:
            val = self.data[fld] if fld in self.data else None
            if val is not None:
                setattr(who, fld, val)

        who.save()
        return who
