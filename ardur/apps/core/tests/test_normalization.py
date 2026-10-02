from decimal import Decimal
from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from ardur.apps.financiera.normalization import fallecido, dinero, identificador

class NormalizationTests(SimpleTestCase):
    def test_deceased_both_markers(self):
        self.assertTrue(fallecido('PERSONA (+)'))
        self.assertTrue(fallecido('PERSONA +'))
        self.assertFalse(fallecido('PERSONA'))
    def test_identifiers_keep_leading_zeros(self):
        self.assertEqual(identificador(' 001234 '), '001234')
    def test_decimal_not_float(self):
        self.assertEqual(dinero('0.15'), Decimal('0.15'))
        for value in ('NaN', '1,234.00', '-1', '=SUM(A1)', '0.001'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                dinero(value)
