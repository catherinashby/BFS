import json
from datetime import date

from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from django.urls import path

from accounts.models import User
from ..apis import Preparer, QSencoder, ApiError, ApiBase
from ..models import Identifier


class TestPreparer(TestCase):

    def test_prepare(self):
        d = {'barcode': 'barcode', 'linked_code': 'linked_code'}

        prep = Preparer(None)
        rc = prep.prepare(d)
        self.assertDictEqual(rc, d, "should return data unchanged")

        id_dict = {'barcode': '1007', 'linked_code': 'UPC'}
        id = Identifier(barcode=id_dict['barcode'],
                        linked_code=id_dict['linked_code'])
        prep = Preparer(d)
        rc = prep.prepare(id)
        self.assertDictEqual(rc, id_dict)

        rcd_dict = {'id': 100, 'identifier': id.get_absolute_url()}
        rcd = {'id': rcd_dict['id'], 'identifier': id}
        flds = {'id': 'id', 'identifier': 'identifier'}
        rc = prep.prepare(rcd, flds)
        self.assertDictEqual(rc, rcd_dict)
        return

    def test_extract_data(self):

        class SimpleObject(object):
            count = 1
            result = object()

        class TestObject(object):
            options = {'first': 1, 'last': 99}
            child = SimpleObject()

            def say(self):
                return 'testing....'

        to = TestObject()
        prep = Preparer(None)

        rc = prep.extract_data('.', 'text')
        self.assertEquals(rc, 'text', "should return data unchanged")
        rc = prep.extract_data('count', None)
        self.assertIsNone(rc, "should handle null case")
        rc = prep.extract_data('say', to)
        self.assertEquals(rc, to.say(), "should return function result")
        # test parsing of dotted names
        rc = prep.extract_data('options.last', to)
        self.assertEquals(rc, 99, "should handle dictionary entries")
        rc = prep.extract_data('child.result.__class__', to)
        self.assertIsInstance(rc, object, "should handle multiple dot-levels")


class TestQSencoder(TestCase):

    def test_QSencoder(self):
        jdp = {}
        id = Identifier(barcode='000')
        url = id.get_absolute_url()
        result = json.dumps(id, cls=QSencoder, **jdp).strip('"')
        self.assertEquals(result, url)

        usr = User.objects.create_user(username='dorothy',
                                       email='dot@kansas.gov',
                                       is_active=True,
                                       password='rubySlippers')
        result = json.dumps(usr, cls=QSencoder, **jdp).strip('"')
        self.assertEquals(result, '1')

        now = date.today()
        txt = now.isoformat()
        result = json.dumps(now, cls=QSencoder, **jdp).strip('"')
        self.assertEquals(result, txt)


class TestApiError(TestCase):

    def err_func(self, msg=None):
        raise ApiError(msg)

    def test_empty_message(self):
        with self.assertRaisesMessage(ApiError, 'Api Error') as ctx:
            self.err_func()

    def test_with_message(self):
        with self.assertRaisesMessage(ApiError, 'custom message') as ctx:
            self.err_func('custom message')


class TestApiBase(TestCase):

    def test_init(self):
        api = ApiBase()
        self.assertIsInstance(api, ApiBase)

    def test_classmethods(self):
        name = ApiBase.build_url_name('list')
        self.assertEquals(name, 'api_base_list')

        pathlist = ['base', 'base/<int:pk>']
        urls = ApiBase.urls()
        paths = [x.pattern._route for x in urls]
        for path in paths:
            self.assertIn(path, pathlist, "{} should be a route".format(path))

    def test_handler(self):

        rf = RequestFactory()
        func = ApiBase.as_list()

        resp = func(rf.options('check'))
        self.assertIsInstance(resp, JsonResponse, "should return JsonResponse")
        d = json.loads(resp.content)
        self.assertIn('error', d, "should contain error message")
        self.assertEquals(d['error'], "The specified HTTP method OPTIONS is not implemented.")

        with self.settings(DEBUG=True):
            resp = func(rf.post({}))
            self.assertIsInstance(resp, JsonResponse, "should return JsonResponse")
            d = json.loads(resp.content)
            self.assertIn('error', d, "should contain error message")
            self.assertEquals(d['error'], "Unauthorized")
            self.assertIn('traceback', d, "should contain traceback")

        resp = func(rf.get('base'))
        self.assertIsInstance(resp, JsonResponse, "should return JsonResponse")
        d = json.loads(resp.content)
        self.assertIn('error', d, "should contain error message")
        self.assertEquals(d['error'], 'The "list" method is not implemented.')
