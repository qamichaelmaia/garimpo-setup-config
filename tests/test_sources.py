import unittest

from src.sources import _parse_price


class ParsePriceTests(unittest.TestCase):
    def test_parses_brazilian_currency(self):
        self.assertEqual(_parse_price("Oferta por R$ 1.234,56"), 1234.56)

    def test_returns_none_without_price(self):
        self.assertIsNone(_parse_price("Produto em promoção"))


if __name__ == "__main__":
    unittest.main()
