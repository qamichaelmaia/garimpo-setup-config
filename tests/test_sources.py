import io
import json
import unittest
from unittest.mock import patch

from src.sources import _matches_item, collect_offers


class CollectOffersTests(unittest.TestCase):
    def test_memory_item_does_not_match_motherboards(self):
        memory_item = {
            "keywords": ["memória", "RAM"],
            "required_keywords": ["DDR5"],
            "exclude_keywords": ["notebook", "laptop"],
        }

        self.assertTrue(
            _matches_item("Memória Corsair DDR5 16GB", memory_item)
        )
        self.assertFalse(
            _matches_item("Placa Mãe MSI B760M DDR5", memory_item)
        )

    @patch("src.sources.urlopen")
    def test_returns_only_active_matching_store_promotions(self, urlopen):
        search_results = {
            "data": {
                "deals": [
                    {
                        "slug": "active-gpu",
                        "title": "Placa de Vídeo RTX 5060 8GB",
                        "kind": "promotion",
                        "status": "active",
                        "price": 2499,
                        "sourceUrl": "https://store.example/gpu",
                    },
                    {
                        "slug": "expired-gpu",
                        "title": "RTX 5060 Ti expirada",
                        "kind": "promotion",
                        "status": "expired",
                        "price": 2000,
                        "sourceUrl": "https://store.example/expired",
                    },
                    {
                        "slug": "discussion",
                        "title": "RTX 5060 vale a pena?",
                        "kind": "discussion",
                        "status": "active",
                        "price": 2000,
                        "sourceUrl": "https://store.example/discussion",
                    },
                    {
                        "slug": "notebook",
                        "title": "Notebook gamer RTX 5060",
                        "kind": "promotion",
                        "status": "active",
                        "price": 7000,
                        "sourceUrl": "https://store.example/notebook",
                    },
                ]
            }
        }
        details = {
            "data": {
                "id": "offer-id",
                "slug": "active-gpu",
                "title": "Placa de Vídeo RTX 5060 8GB",
                "kind": "promotion",
                "status": "active",
                "price": 2499,
                "sourceUrl": "https://store.example/gpu",
                "store": {"name": "Loja Exemplo"},
                "couponCode": "GPU10",
                "imageUrl": "https://store.example/gpu.jpg",
            }
        }

        def fake_urlopen(request, timeout):
            body = details if "/deals/" in request.full_url else search_results
            return io.BytesIO(json.dumps(body).encode("utf-8"))

        urlopen.side_effect = fake_urlopen
        offers = collect_offers(
            [
                {
                    "name": "RTX 5060",
                    "query": "RTX 5060",
                    "keywords": ["RTX 5060"],
                    "exclude_keywords": ["RTX 5060 Ti", "notebook"],
                }
            ]
        )

        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]["store"], "Loja Exemplo")
        self.assertEqual(offers[0]["coupon_code"], "GPU10")
        self.assertEqual(offers[0]["buy_url"], "https://store.example/gpu")
        self.assertEqual(offers[0]["url"], "https://www.pelando.com.br/d/active-gpu")
        self.assertEqual(urlopen.call_count, 2)


if __name__ == "__main__":
    unittest.main()
