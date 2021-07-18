from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.response import TemplateResponse

from .models import Identifier
from .apis import QSencoder


@login_required
def index(request):
    context = {}
    template = "inventory/index.html"

    return TemplateResponse(request, template, context)


def prepare(inst, cf):
    result = {}
    for fld in cf:
        name = fld.name
        val = getattr(inst, name, None)
        result[name] = val
    return result


# GET /inventory/identifier/<pk>/
def identifier_detail(request, pk):
    one = Identifier.idents.get(barcode=pk)
    fields = prepare(one, one._meta.concrete_fields)
    resp = JsonResponse(fields, encoder=QSencoder)
    return resp
