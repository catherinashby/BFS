from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse


@login_required
def index(request):
    context = {}
    template = "inventory/index.html"

    return TemplateResponse(request, template, context)
