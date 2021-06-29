import json
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
from django.conf.urls import url
from django.urls import reverse
from django.apps import apps
from restless.preparers import Preparer
from restless.dj import DjangoResource
from restless.resources import Data


class RestlessPreparer ( Preparer ):
    """
    This takes a ``fields`` parameter, which should be a dictionary of
    keys ( fieldnames to expose to the user ) & values ( a dotted lookup path to
    the desired attribute/key on the object ).

    Example::

        preparer = RestlessPreparer ( fields={
            # ``user`` is the key the client will see.
            # ``:author.pk`` is the dotted path lookup ``FieldsPreparer``
            # will traverse on the data to return a value.
            # the leading ':' on the "author" field means that it may be null
            'user': ':author.pk',
        } )

    """
    def __init__ ( self, fields ):
        super ( RestlessPreparer, self ).__init__()
        self.fields = fields

    def prepare ( self, data ):
        """
        Handles transforming the provided data into the fielded data that should
        be exposed to the end user.

        Uses the ``lookup_data`` method to traverse dotted paths.

        Returns a dictionary of data as the response.
        """
        result = {}

        if not self.fields: # No fields specified. Serialize everything.
            return data

        for fieldname, lookup in self.fields.items():
            if isinstance ( lookup, str ):
                result[fieldname] = self.lookup_data ( lookup, data )
            else:
                result[fieldname] = self.lookup_field ( lookup, data )

        return result

    def lookup_data ( self, lookup, data ):
        """
        Given a lookup string, attempts to descend through nested data looking for
        the value.

        Can work with either dictionary-alikes or objects ( or any combination of
        those ).

        Lookups should be a string. If it is a dotted path, it will be split on
        ``.`` & it will traverse through to find the final value. If not, it will
        simply attempt to find either a key or attribute of that name & return it.

        Example::

            >>> data = {
            ...     'type': 'message',
            ...     'greeting': {
            ...         'en': 'hello',
            ...         'fr': 'bonjour',
            ...         'es': 'hola',
            ...     },
            ...     'person': Person ( 
            ...         name='daniel'
            ...   )
            ... }
            >>> lookup_data ( 'type', data )
            'message'
            >>> lookup_data ( 'greeting.en', data )
            'hello'
            >>> lookup_data ( 'person.name', data )
            'daniel'

        """
        value = data
        parts = lookup.split ( '.' )

        if not parts or not parts[0]:
            return value

        null_ok = False
        callable_part = False
        part = parts[0]
        remaining_lookup = '.'.join ( parts[1:] )
        if part.startswith ( ':' ):
            null_ok = True
            part = part.lstrip ( ':' )
        if part.startswith ( '+' ):
            callable_part = True
            part = part.lstrip ( '+' )

        if hasattr ( data, 'keys' ) and hasattr ( data, '__getitem__' ):
            # Dictionary enough for us.
            value = data[part]
        else:
            # Assume it's an object.
            value = getattr ( data, part )
        if callable_part:
            fnc = value
            value = fnc()

        if not value:
            if null_ok:
                return value
            
        if not remaining_lookup:
            return value

        # There's more to lookup, so dive in recursively.
        return self.lookup_data ( remaining_lookup, value )

    def lookup_field ( self, lookup, data ):
        value = getattr ( data, lookup.name, None )
        meta = lookup.model._meta
        if lookup.primary_key:
            fmt = '{}:{}_detail'.format ( meta.app_label, meta.model_name )
            url = reverse ( fmt, args=[ str ( data.pk ) ] )
            return self.make_absolute ( url )
        if not hasattr ( lookup, 'to_fields' ):
            return value
#       foreign keys
        meta = value._meta
        fmt = '{}:{}_detail'.format ( meta.app_label, meta.model_name )
        try:
            url = reverse ( fmt, args=[ str ( value.pk ) ] )
            return self.make_absolute ( url )
        except:
            return None

class RestlessResource ( DjangoResource ):
    """
    A simple class-based view for use as a base
    """
    _model = None
    fields = None

    @classmethod
    def urls ( cls, name_prefix=None ):
        name = cls.__name__.replace ( 'Object', '' ).lower()
        if not name_prefix: name_prefix = name
        list_regex = "^{}/$".format ( name )
        detail_regex = "^{}/ ( ?P<pk>\d+ )/$".format ( name )
        return [
            url ( list_regex, cls.as_list(), name=cls.build_url_name ( 'list', name_prefix ) ),
            url ( detail_regex, cls.as_detail(), name=cls.build_url_name ( 'detail', name_prefix ) ),
        ]

    def __init__ ( self, *args, **kwargs ):
        super().__init__()
        if not self.fields and self._model:
            self.fields = dict()
            for fld in self._model._meta.fields:
                self.fields[ fld.name ] = fld
                if fld.primary_key:
                    self.fields[ 'url' ] = fld
                    self.fields[ fld.name ] = fld.attname
                if hasattr ( fld, '_related_fields' ):
                    self.fields[ fld.attname ] = fld.attname
                
        self.preparer = RestlessPreparer ( self.fields )
        
    def is_authenticated ( self ):
        method = self.request_method()
        if method == 'GET': return True
        allowed = [ 'PUT', 'POST' ]
        if hasattr ( self, 'can_delete' ) and self.can_delete:
            allowed.append ( 'DELETE' )
        perhaps = False
        for verb in allowed:
            if verb == method:
                perhaps = True
        if perhaps:
            perhaps = self.request.user.is_authenticated
        return perhaps

    def wrap_list_response ( self, data ):
        """
        Takes a list of data & wraps it in a dictionary ( within the ``objects``
        key ).

        :param data: A list of data about to be serialized
        :type data: list

        :returns: A wrapping dict
        :rtype: dict
        """
        return {
            "count": len ( data ),
            "objects": data
        }
    
    def list ( self, *args, **kwargs ):
        """
        Returns the data for a GET on a list-style endpoint.

        :returns: A collection of data
        :rtype: list or iterable
        """
        if not self._model:
            raise NotImplementedError ( 
                  'subclasses of RestlessResource must set a _model value' )
        self.preparer.make_absolute = self.request.build_absolute_uri
        rcd = self._model.objects.all()
        return rcd
        
    def detail ( self, *args, **kwargs ):
        """
        Returns the data for a GET on a detail-style endpoint.

        :returns: An item
        :rtype: object or dict
        """
        if not self._model:
            raise NotImplementedError ( 
                  'subclasses of RestlessResource must set a _model value' )
        self.preparer.make_absolute = self.request.build_absolute_uri
        pk = kwargs[ 'pk' ]
        try: rcd = self._model.objects.get ( pk=pk )
        except: return None
        return rcd

    def create ( self, *args, **kwargs ):
        """
        Allows for creating data via a POST on a list-style endpoint.

        :returns: May return the created item or ``None``
        """
        if not self._model:
            raise NotImplementedError ( 
                  'subclasses of RestlessResource must set a _model value' )

        self.preparer.make_absolute = self.request.build_absolute_uri
        data = self.data
        if not isinstance ( data, dict ):
            return Data ( { 'error': "Only one new record allowed" },
                         should_prepare=False )
        rcd = self._model()
        for fld in data:
            if hasattr ( rcd, fld ):
                setattr ( rcd, fld, data[ fld ] )
        try: rcd.full_clean()
        except ValidationError as e:    # pragma: no cover
            return Data ( { 'error': list ( e.message_dict ) }, should_prepare=False )
        try: rcd.save()
        except Exception as e:    # pragma: no cover
            return Data ( { 'error': list ( e.args ) }, should_prepare=False )
        return rcd

    def update ( self, *args, **kwargs ):
        """
        Updates existing data for a PUT on a detail-style endpoint.

        :returns: May return the updated item or ``None``
        """
        if not self._model:
            raise NotImplementedError ( 
                  'subclasses of RestlessResource must set a _model value' )

        self.preparer.make_absolute = self.request.build_absolute_uri
        pk = kwargs[ 'pk' ]
        try: rcd = self._model.objects.get ( pk=pk )
        except: return None
        for fld in self.data:
            if hasattr ( rcd, fld ):
                setattr ( rcd, fld, self.data[ fld ] )
        try: rcd.save()
        except Exception as e:    # pragma: no cover
            return Data ( { 'error': list ( e.args ) }, should_prepare=False )
        return rcd


    def delete ( self, *args, **kwargs ):
        """
        Deletes data for a DELETE on a detail-style endpoint.
        """
        return None
     

    def update_list ( self, *args, **kwargs ):
        """
        Updates the entire collection for a PUT on a list-style endpoint.
        """
        err = { 'error': '"update_list" method ( list,PUT ) not implemented' }
        return Data ( err, should_prepare=False )

    def create_detail ( self, *args, **kwargs ):
        """
        Creates a subcollection of data for a POST on a detail-style endpoint.
        """
        err = { 'error': '"create_detail" method ( detail,POST ) not implemented' }
        return Data ( err, should_prepare=False )

    def delete_list ( self, *args, **kwargs ):
        """
        Deletes *ALL* data in the collection for a DELETE on a list-style
        endpoint.
        """
        return None

class APIObject ( RestlessResource ):

    @classmethod
    def urls ( cls, name_prefix=None ):
        return [ url ( r'^$', cls.as_detail(), name='api' ), ]

    def list ( self, *args, **kwargs ):
        return {'error': '"list" method {list,PUT} not implemented'}

    def detail ( self, *args, **kwargs ):
        d = dict()
        for lbl in self.models:
            url = reverse ( '{}:{}_list'.format ( self.app, lbl ) )
            d[ lbl ] = self.request.build_absolute_uri ( url )
        return d

    def create ( self, *args, **kwargs ):
        return {'error': '"create" method {list,POST} not implemented'}

    def update ( self, *args, **kwargs ):
        return {'error': '"update" method {detail,PUT} not implemented'}


top_urls = dict()

def gather_top_urls ( *args, **kwargs ):
    
    for app in apps.get_app_configs():
        try:
            url = reverse ( "{}:api".format ( app.name ) )
            top_urls[ app.verbose_name ] = url
        except:
            pass
    return

def list_modules ( request ):
    d = dict()
    for lbl, url in top_urls.items():
        d[ lbl ] = request.build_absolute_uri ( url )
    return d

def api ( request, json_in=None ):
    jsondata = json_in
    if jsondata:
        if isinstance ( json_in, ( str ) ):
            jsondata = json.loads ( json_in )
    else:
        jsondata = list_modules ( request )
    context = { 'request': request }
    crumbs = []
    path = "" if request.path == "/api/" else request.path.rstrip ( '/' )
    while path:
        url = '{}/'.format ( request.build_absolute_uri ( path ) )
        dirs = path.split ( '/' )
        name = dirs.pop()
        crumbs.append ( ( name, url ) )
        path = '/'.join ( dirs )
    url = request.build_absolute_uri ( '/api/' )
    breadcrumbs = [ ( "API Root", url ) ]
    last_name = None; ix = 0
    while crumbs:
        pair = crumbs.pop()
        name = pair[0].title()
        if len ( name ) < 4: name = pair[0]
        if ix == 0: breadcrumbs.append ( ( 'Module {}'.format ( name ), pair[1] ) )
        if ix == 1: breadcrumbs.append ( ( '{} List'.format ( name ), pair[1] ) )
        if ix == 2: breadcrumbs.append ( ( '{} Instance'.format ( last_name ), pair[1] ) )
        last_name = name; ix += 1
    context[ 'breadcrumbs' ] = breadcrumbs
    context[ 'json' ] = jsondata
    if len ( breadcrumbs ) == 3: #    list; may need pagination
        api_pagination ( context, request.GET )
    return render ( request, 'api.html', context )

def api_pagination ( context, gets ):
    MAX_PER_PAGE = 50
    datadict = context[ 'json' ]
    count = datadict[ 'count' ]
    if count <= MAX_PER_PAGE:  return
    
    paginator = Paginator ( datadict['objects'], MAX_PER_PAGE )
    try: page = gets[ 'page' ]
    except: page = 1
    try: objs = paginator.page ( page )
    except PageNotAnInteger:    # If page is not an integer, deliver first page.
        objs = paginator.page ( 1 )
    except EmptyPage:   # If page is out of range ( e.g. 9999 ), deliver last page of results.
        objs = paginator.page ( paginator.num_pages )
    context[ 'json' ][ 'objects' ] = objs.object_list

    currpage = objs.number
    prevpage = currpage - 1
    nextpage = currpage + 1
    lastpage = paginator.num_pages
    count = len ( context[ 'breadcrumbs' ] ) - 1
    pager = {
        'url': context[ 'breadcrumbs' ][ count ][ 1 ],
        'curr': currpage, 'last': lastpage
        }
    if prevpage > 0:  pager[ 'prev' ] = prevpage
    if nextpage < lastpage: pager[ 'next' ] = nextpage

    context[ 'pager' ] = pager
    return
