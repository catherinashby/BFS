from django.test import TestCase

from ..utils import check_digit


class CheckDigitTest(TestCase):

    def test_check_digit(self):
        result = check_digit('4-A')
        self.assertEqual(result, -1, "check_digit only accepts digitstrings")
        loc = '572'
        result = check_digit('572')
        self.assertEqual(result, 4, "Algorithm should return '4'")
        result = check_digit('4028736')
        self.assertEqual(result, 0, "Algorithm should return '0'")
        return
