from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.template.response import TemplateResponse

from .models import Identifier, Location, Supplier


@login_required
def index(request):
    context = {}
    template = "inventory/index.html"

    return TemplateResponse(request, template, context)


@login_required
def shelves(request):
    context = {}
    template = "inventory/shelves.html"

    shelves = Location.objects.all()
    paginator = Paginator(shelves, 25)  # Show 25 locations per page.
    page_number = request.GET.get('page')
    context['page_obj'] = paginator.get_page(page_number)

    return TemplateResponse(request, template, context)


@login_required
def suppliers(request):
    context = {}
    template = "inventory/suppliers.html"

    shelves = Supplier.objects.all()
    paginator = Paginator(shelves, 25)  # Show 25 locations per page.
    page_number = request.GET.get('page')
    context['page_obj'] = paginator.get_page(page_number)

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
