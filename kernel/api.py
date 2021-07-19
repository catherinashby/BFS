import sys
import traceback
from functools import wraps

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt


class Preparer(object):

    def __init__(self, fields):
        self.fields = fields

    def prepare(self, data, fieldlist=None):
        """
        Handles transforming the provided data into the fielded data that should
        be exposed to the end user.
        """
        fields = fieldlist if fieldlist else (
             self.fields if self.fields else None)
        if not isinstance(fields, dict):  # No fields specified -- do nothing.
            return data

        result = {}
        for keyname, lookup in fields.items():
            result[keyname] = self.extract_data(lookup, data)

        return result

    def extract_data(self, lookup, data):
        """
        Given a lookup string, attempts to descend through nested data looking
        for the value.
            lookup:  a non-empty string, without leading dot(s)
            data: anything
        """
        chunks = lookup.split('.')
        if not chunks[0]:
            return data
        chunk = chunks[0]                   # what we're looking for
        remaining = '.'.join(chunks[1:])    # what we'll do later

        value = getattr(data, 'keys', None)
        if callable(value) and hasattr(data, '__getitem__'):
            value = data[chunk]             # a dictionary(-like) object
        elif data is not None:
            value = getattr(data, chunk)    # a generic object
        else:
            value = None                    # nothing at all

        # Call if it's callable except if it's a Django DB manager instance
        #   We check if is a manager by checking the db_manager (duck typing)
        if callable(value) and not hasattr(value, 'db_manager'):
            value = value()

        if not remaining:
            # See if it needs to be urlized
            if hasattr(value, 'get_absolute_url'):
                value = value.get_absolute_url()
            return value

        # There's more to lookup, so dive in recursively.
        return self.extract_data(remaining, value)


class ApiError(Exception):
    msg = "Api Error"

    def __init__(self, msg=None):
        if not msg:
            msg = self.__class__.msg
        super(ApiError, self).__init__(msg)


class ApiBase(object):

    http_methods = {
        'list': {
            'GET': 'list',
            'POST': 'create',
            'PUT': 'update_list',
            'DELETE': 'delete_list',
        },
        'detail': {
            'GET': 'detail',
            'POST': 'create_detail',
            'PUT': 'update',
            'DELETE': 'delete',
        }
    }
    preparer = Preparer(None)
    serializer = DjangoJSONEncoder

    def __init__(self, *args, **kwargs):
        self.init_args = args
        self.init_kwargs = kwargs
        self.request = None

    @classmethod
    def build_url_name(cls, name, name_prefix=None):
        if name_prefix is None:
            name_prefix = 'api_{0}'.format(
                cls.__name__.replace('Api', '').lower()
            )

        name_prefix = name_prefix.rstrip('_')
        return '_'.join([name_prefix, name])

    @classmethod
    def urls(cls, name_prefix=None):
        base_name = cls.__name__.replace('Api', '')
        name = base_name.strip('_').lower()
        lst = path(name, cls.as_list(), name=cls.build_url_name('list', name))
        dtl = path('{}/<int:pk>'.format(name), cls.as_detail(),
                   name=cls.build_url_name('detail', name))
        return [lst, dtl]

    @classmethod
    def as_list(cls, *args, **kwargs):
        return csrf_exempt(
            cls.as_view('list', *args, **kwargs)
            )

    @classmethod
    def as_detail(cls, *args, **kwargs):
        return csrf_exempt(
            cls.as_view('detail', *args, **kwargs)
            )

    @classmethod
    def as_view(cls, view_type, *init_args, **init_kwargs):

        @wraps(cls)
        def _wrapper(request, *args, **kwargs):
            # Make a new instance so that no state potentially leaks between
            # instances.
            inst = cls(*init_args, **init_kwargs)
            inst.request = request
            return inst.handle(view_type, *args, **kwargs)

        return _wrapper

    def handle(self, endpoint, *args, **kwargs):
        method = self.request.method.upper()
        try:
            # Use ``.get()`` so we can also dodge potentially incorrect
            # ``endpoint`` errors as well.
            if method not in self.http_methods.get(endpoint, {}):
                msg = "The specified HTTP method {} is not implemented.".format(method)
                raise ApiError(msg)
            if not self.is_authenticated():
                raise ApiError('Unauthorized')
            view_method = getattr(self, self.http_methods[endpoint][method])
            data = view_method(*args, **kwargs)

        except ApiError as err:
            data = self.build_error(err)

        return self.build_response(data)

    def build_error(self, err):
        data = {'error': err.args[0]}
        if settings.DEBUG:  # Add the traceback.
            exc_info = sys.exc_info()
            stack = traceback.format_stack()
            stack = stack[:-2]
            stack.extend(traceback.format_tb(exc_info[2]))
            stack.extend(traceback.format_exception_only(exc_info[0], exc_info[1]))
            stack_str = "Traceback (most recent call last):\n"
            stack_str += "".join(stack)
            # Remove the last \n
            stack_str = stack_str[:-1]
            data['traceback'] = stack_str
        return data

    def build_response(self, data):
        return JsonResponse(data, encoder=self.serializer)

    def is_authenticated(self):
        # Should be overwritten by subclasses
        if self.request.method.upper() == 'GET':
            return True

        return False

    # Common methods the child class should implement.

    def list(self, *args, **kwargs):    # pragma: no cover
        raise ApiError('The "list" method is not implemented.')

    def detail(self, *args, **kwargs):  # pragma: no cover
        raise ApiError('The "detail" method is not implemented.')

    def create(self, *args, **kwargs):  # pragma: no cover
        raise ApiError('The "create" method is not implemented.')

    def update(self, *args, **kwargs):  # pragma: no cover
        raise ApiError('The "update" method is not implemented.')

    def delete(self, *args, **kwargs):  # pragma: no cover
        raise ApiError('The "delete" method is not implemented.')

    # Uncommon methods the child class should implement.
    # These have intentionally uglier method names, which reflects just how
    # much harder they are to get right.

    def update_list(self, *args, **kwargs):     # pragma: no cover
        raise ApiError('The "update_list" method is not implemented.')

    def create_detail(self, *args, **kwargs):   # pragma: no cover
        raise ApiError('The "create_detail" method is not implemented.')

    def delete_list(self, *args, **kwargs):     # pragma: no cover
        raise ApiError('The "delete_list" method is not implemented.')
