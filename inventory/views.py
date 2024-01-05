import json

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.template.response import TemplateResponse

from .models import Identifier, Location, Supplier, ItemTemplate, Picture


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
    paginator = Paginator(shelves, 25)  # Show 25 suppliers per page.
    page_number = request.GET.get('page')
    context['page_obj'] = paginator.get_page(page_number)

    return TemplateResponse(request, template, context)


@login_required
def itemTemplates(request):
    context = {}
    template = "inventory/itemTemplate.html"

    items = ItemTemplate.objects.all()
    paginator = Paginator(items, 25)  # Show 25 items per page.
    page_number = request.GET.get('page')
    context['page_obj'] = paginator.get_page(page_number)

    return TemplateResponse(request, template, context)


@login_required
@ensure_csrf_cookie
def images(request):
    context = {}
    template = "inventory/images.html"

    context['mu'] = settings.MEDIA_URL
    images = Picture.objects.all()
    paginator = Paginator(images, 25)  # Show 25 images per page.
    page_number = request.GET.get('page')
    context['page_obj'] = paginator.get_page(page_number)

    return TemplateResponse(request, template, context)


# POST /inventory/images/upload/
def images_upload(request):
    fields = {'error': 'No file uploaded'}
    image_file = None
    item = None
    for fil in request.FILES:
        image_file = request.FILES[fil]
    for key in request.POST:
        if key == 'item_id':
            item = request.POST[key]

    if image_file:

        one = Picture()
        setattr(one, 'photo', image_file)
        setattr(one, 'item_id', item)
        one.save()

        fields = {}
        fields['id'] = one.id
        fields['item_id'] = one.item_id
        fields['photo'] = one.photo.name
        fields['uploaded'] = one.uploaded

    resp = JsonResponse(fields, encoder=DjangoJSONEncoder)
    return resp


@login_required
def stockbook(request):
    context = {}
    template = "inventory/stockBook.html"
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
