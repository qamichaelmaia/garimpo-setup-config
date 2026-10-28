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

    def test_requires_both_lga1851_and_ddr5_for_motherboards(self):
        motherboard_item = {
            "keywords": ["placa mãe"],
            "required_keywords": ["LGA 1851", "DDR5"],
            "exclude_keywords": ["processador", "cooler"],
        }

        self.assertTrue(
            _matches_item("Placa-Mãe Z890 LGA 1851 DDR5", motherboard_item)
        )
        self.assertFalse(
            _matches_item("Placa-Mãe B760 LGA 1700 DDR5", motherboard_item)
        )
        self.assertFalse(
            _matches_item("Placa-Mãe LGA 1851 DDR4", motherboard_item)
        )

    def test_power_supply_filter_matches_only_requested_wattages(self):
        power_supply_item = {
            "keywords": ["fonte"],
            "required_any_keywords": ["650W", "700W", "750W", "800W"],
        }

        self.assertTrue(
            _matches_item("Fonte Corsair 750W 80 Plus Gold", power_supply_item)
        )
        self.assertFalse(
            _matches_item("Fonte Corsair 850W 80 Plus Gold", power_supply_item)
        )

    def test_rtx_5060_ti_filter_includes_8gb_and_16gb_cards(self):
        video_card_item = {
            "keywords": ["RTX 5060 Ti"],
            "exclude_keywords": ["PC Gamer", "notebook", "laptop"],
        }

        self.assertTrue(
            _matches_item("Placa de Vídeo RTX 5060 Ti 8GB", video_card_item)
        )
        self.assertTrue(
            _matches_item("Placa de Vídeo RTX 5060 Ti 16GB", video_card_item)
        )
        self.assertFalse(
            _matches_item("PC Gamer com RTX 5060 Ti 16GB", video_card_item)
        )

    def test_ventoinha_filter_excludes_cpu_coolers(self):
        fan_item = {
            "keywords": ["fan", "fans", "ventoinha"],
            "exclude_prefix_keywords": ["gabinete"],
            "exclude_keywords": [
                "cooler processador",
                "water cooler",
            ],
        }

        self.assertTrue(
            _matches_item("Kit 3 Fans RGB para gabinete", fan_item)
        )
        self.assertFalse(
            _matches_item("Water Cooler com 3 Fans RGB", fan_item)
        )
        self.assertFalse(
            _matches_item("Gabinete Gamer com 4 Fans RGB", fan_item)
        )
        self.assertFalse(
            _matches_item("Metaphor Refantazio - Playstation 5", fan_item)
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
                    "offer_published": "2026-10-28T11:00:00-0300",
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
        self.assertEqual(offers[0]["published_at"], "2026-10-28T11:00:00-0300")
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
                {
                    "name": "B",
                    "queries": ["shared", "unique"],
                    "keywords": ["B"],
                },
            ]
        )

        self.assertEqual(urlopen.call_count, 3)

    @patch("src.sources.urlopen")
    def test_combines_results_from_multiple_searches(self, urlopen):
        offer_template = {
            "offer_price": 2500,
            "offer_status_name": "APPROVED",
            "store_name": "Loja Exemplo",
        }
        search_results = {
            "first": [
                {
                    **offer_template,
                    "offer_title": "Placa RTX 5060 Ti 8GB",
                    "offer_slug": "rtx-5060-ti-8gb",
                }
            ],
            "second": [
                {
                    **offer_template,
                    "offer_title": "Placa RTX 5060 Ti 16GB",
                    "offer_slug": "rtx-5060-ti-16gb",
                }
            ],
        }

        def fake_urlopen(request, timeout):
            if "promotions?" in request.full_url:
                payload = {"data": []}
            else:
                query = request.full_url.rsplit("q=", 1)[1]
                payload = {"active_offers": search_results[query]}
            return io.BytesIO(json.dumps(payload).encode("utf-8"))

        urlopen.side_effect = fake_urlopen

        offers = collect_offers(
            [
                {
                    "name": "RTX 5060 Ti",
                    "queries": ["first", "second"],
                    "keywords": ["RTX 5060 Ti"],
                }
            ]
        )

        self.assertEqual(len(offers), 2)
        self.assertEqual(
            {offer["title"] for offer in offers},
            {"Placa RTX 5060 Ti 8GB", "Placa RTX 5060 Ti 16GB"},
        )
        self.assertEqual(urlopen.call_count, 3)

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
                        "createdAt": "2026-10-28T14:00:00.000Z",
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
        self.assertEqual(offers[0]["published_at"], "2026-10-28T14:00:00.000Z")
        self.assertEqual(offers[0]["price"], 2499.9)
        self.assertEqual(offers[0]["store"], "Mercado Livre")
        self.assertEqual(offers[0]["coupon_code"], "GPU10")
        self.assertEqual(offers[0]["url"], "https://descpromo.com/r/abc123")


if __name__ == "__main__":
    unittest.main()
