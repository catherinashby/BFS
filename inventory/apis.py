from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse

from .models import Identifier


class QSencoder(DjangoJSONEncoder):
    """
    JSONEncoder subclass that knows how to encode
    instances (FKs and M2Ms)
    as well as date/time, decimal types, and UUIDs.
    """
    def default(self, obj):
        if hasattr(obj, '_meta'):
            # possible keyField
            if hasattr(obj, 'get_absolute_url'):
                return obj.get_absolute_url()
            pk = str(obj.pk) if hasattr(obj, 'pk') else None
            return pk
        return super().default(obj)

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

