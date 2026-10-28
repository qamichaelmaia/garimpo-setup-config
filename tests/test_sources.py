import io
import json
import unittest
from unittest.mock import patch

from src.sources import _matches_item, _parse_price, collect_offers


class CollectOffersTests(unittest.TestCase):
    def test_parses_bilometro_brazilian_prices(self):
        self.assertEqual(_parse_price("R$ 1.380"), 1380.0)
        self.assertEqual(_parse_price("R$ 2.499,90 no Pix"), 2499.9)
        self.assertIsNone(_parse_price("Preço não informado"))

    def test_product_filters_exclude_other_product_types(self):
        memory_item = {
            "keywords": ["DDR5"],
            "required_keywords": ["memória"],
            "exclude_keywords": ["notebook", "placa mãe"],
        }

        self.assertTrue(
            _matches_item("Memória Corsair DDR5 16GB", memory_item)
        )
        self.assertFalse(
            _matches_item("Placa-Mãe Gigabyte DDR5", memory_item)
        )

    @patch("src.sources.urlopen")
    def test_returns_matching_store_offers_with_coupon_and_image(self, urlopen):
        promobit_payload = {
            "active_offers": [
                {
                    "offer_id": 1,
                    "offer_title": "Placa de Vídeo RTX 5060 8GB",
                    "offer_slug": "rtx-5060-8gb-1",
                    "offer_price": 2499,
                    "offer_coupon": "GPU10",
                    "offer_photo": "/gpu.jpg",
                    "offer_status_name": "APPROVED",
                    "store_name": "Loja Exemplo",
                },
                {
                    "offer_id": 2,
                    "offer_title": "Notebook gamer RTX 5060",
                    "offer_slug": "notebook-rtx-5060-2",
                    "offer_price": 7000,
                    "offer_status_name": "APPROVED",
                    "store_name": "Loja Exemplo",
                },
                {
                    "offer_id": 3,
                    "offer_title": "PC Gamer RTX 5060 Ti",
                    "offer_slug": "pc-gamer-rtx-5060-ti-3",
                    "offer_price": 8000,
                    "offer_status_name": "APPROVED",
                    "store_name": "Loja Exemplo",
                },
                {
                    "offer_id": 4,
                    "offer_title": "Placa RTX 5060 8GB sem preço",
                    "offer_slug": "no-price-4",
                    "offer_price": None,
                    "offer_status_name": "APPROVED",
                    "store_name": "Loja Exemplo",
                },
            ]
        }
        responses = {
            "promotions?": {"data": []},
            "/search?": promobit_payload,
        }

        def fake_urlopen(request, timeout):
            payload = next(
                body for path, body in responses.items() if path in request.full_url
            )
            return io.BytesIO(json.dumps(payload).encode("utf-8"))

        urlopen.side_effect = fake_urlopen
        item = {
            "name": "RTX 5060",
            "query": "RTX 5060",
            "keywords": ["RTX 5060"],
            "exclude_keywords": ["RTX 5060 Ti", "notebook", "PC Gamer"],
        }

        offers = collect_offers([item])

        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]["store"], "Loja Exemplo")
        self.assertEqual(offers[0]["coupon_code"], "GPU10")
        self.assertEqual(offers[0]["image_url"], "https://i.promobit.com.br/268/gpu.jpg")
        self.assertEqual(
            offers[0]["url"],
            "https://www.promobit.com.br/oferta/rtx-5060-8gb-1/",
        )
        self.assertEqual(urlopen.call_count, 2)

    @patch("src.sources.urlopen")
    def test_caches_search_for_shared_queries(self, urlopen):
        responses = {
            "promotions?": {"data": []},
            "/search?": {"active_offers": []},
        }

        def fake_urlopen(request, timeout):
            payload = next(
                body for path, body in responses.items() if path in request.full_url
            )
            return io.BytesIO(json.dumps(payload).encode("utf-8"))

        urlopen.side_effect = fake_urlopen

        collect_offers(
            [
                {"name": "A", "query": "shared", "keywords": ["A"]},
                {"name": "B", "query": "shared", "keywords": ["B"]},
            ]
        )

        self.assertEqual(urlopen.call_count, 2)

    @patch("src.sources.urlopen")
    def test_includes_matching_bilometro_post(self, urlopen):
        responses = {
            "promotions?": {
                "data": [
                    {
                        "gameName": "Placa de vídeo RTX 5060 8GB",
                        "priceDetails": "R$ 2.499,90 no Pix",
                        "purchaseLink": "https://descpromo.com/r/abc123",
                        "couponCode": "GPU10",
                        "imageUrl": "https://images.example/gpu.jpg",
                        "storeName": "Mercado Livre",
                        "status": "SENT",
                    },
                    {
                        "gameName": "Placa de vídeo RTX 5060 Ti 8GB",
                        "priceDetails": "R$ 2.899,00",
                        "purchaseLink": "https://descpromo.com/r/expired",
                        "storeName": "KaBuM!",
                        "status": "EXPIRED",
                    },
                    {
                        "gameName": "Placa RTX 5060 sem preço",
                        "priceDetails": None,
                        "purchaseLink": "https://descpromo.com/r/no-price",
                        "storeName": "Shopee",
                        "status": "SENT",
                    },
                ]
            },
            "/search?": {"active_offers": []},
        }

        def fake_urlopen(request, timeout):
            payload = next(
                body for path, body in responses.items() if path in request.full_url
            )
            return io.BytesIO(json.dumps(payload).encode("utf-8"))

        urlopen.side_effect = fake_urlopen
        item = {
            "name": "RTX 5060",
            "query": "RTX 5060",
            "keywords": ["RTX 5060"],
            "exclude_keywords": ["RTX 5060 Ti"],
        }

        offers = collect_offers([item])

        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]["source"], "bilometro")
        self.assertEqual(offers[0]["price"], 2499.9)
        self.assertEqual(offers[0]["store"], "Mercado Livre")
        self.assertEqual(offers[0]["coupon_code"], "GPU10")
        self.assertEqual(offers[0]["url"], "https://descpromo.com/r/abc123")


if __name__ == "__main__":
    unittest.main()
