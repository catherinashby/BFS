from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.template.response import TemplateResponse

from restless.dj import DjangoResource
from restless.preparers import FieldsPreparer

from .models import Identifier


@login_required
def index(request):
    context = {}
    template = "inventory/index.html"

    return TemplateResponse(request, template, context)


# GET /inventory/identifier/<pk>/
def identifier_detail(request, pk):
    one = Identifier.idents.get(barcode=pk)
    fields = {}
    for fld in one._meta.concrete_fields:
        name = fld.name
        val = getattr(one, name, None)
        fields[name] = val
    resp = JsonResponse(fields, encoder=DjangoJSONEncoder)
    return resp


class LocIdResource(DjangoResource):
    preparer = FieldsPreparer(fields={
        'barcode': 'barcode',
    })

    def is_authenticated(self):
        if self.request.method == 'GET':
            return True
        user = self.request.user
        ok = user.has_perm('inventory.add_identifier')
        return ok

    def request_body(self):

        body = super(LocIdResource, self).request_body()

        return b''

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
        locId = Identifier.locIDs.create(barcode=bc)
        return locId

