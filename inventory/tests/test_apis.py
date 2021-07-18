import json
from datetime import date

from django.http import JsonResponse
from django.test import RequestFactory, TestCase

from accounts.models import User
from ..apis import QSencoder, prepare, identifier_detail
from ..models import Identifier


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


class IdentifierAPITest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.rf = RequestFactory()
        cls.id = Identifier.idents.create(barcode='1007')

    def test_get_identifier(self):
        pk = '1007'
        url = '/inventory/identifier/{}/'.format(pk)
        req = self.rf.get(url)
        resp = identifier_detail(req, pk)
        self.assertIsInstance(resp, JsonResponse, "should be a JsonResponse")
        self.assertEquals(resp.status_code, 200, "response should succeed")

