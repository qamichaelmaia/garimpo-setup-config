import io
import json
import unittest
from unittest.mock import patch

from src.sources import _matches_item, collect_offers


class CollectOffersTests(unittest.TestCase):
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
        payload = {
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
        response = io.BytesIO(json.dumps(payload).encode("utf-8"))
        urlopen.return_value.__enter__.return_value = response
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
        self.assertEqual(urlopen.call_count, 1)

    @patch("src.sources.urlopen")
    def test_caches_search_for_shared_queries(self, urlopen):
        payload = {"active_offers": []}
        response = io.BytesIO(json.dumps(payload).encode("utf-8"))
        urlopen.return_value.__enter__.return_value = response

        collect_offers(
            [
                {"name": "A", "query": "shared", "keywords": ["A"]},
                {"name": "B", "query": "shared", "keywords": ["B"]},
            ]
        )

        self.assertEqual(urlopen.call_count, 1)


if __name__ == "__main__":
    unittest.main()
