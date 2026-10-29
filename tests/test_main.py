import unittest
from datetime import date

from src.main import _prioritize_offers


class PrioritizeOffersTests(unittest.TestCase):
    def test_prioritizes_rx_9060_xt_with_rtx_5060_ti(self):
        offers = [
            {
                "item": "Placa de vídeo RTX 5060",
                "published_at": "2026-10-28T20:00:00Z",
            },
            {
                "item": "Placa de vídeo RX 9060 XT 16GB",
                "published_at": "2026-10-28T15:00:00-03:00",
            },
            {
                "item": "Placa de vídeo RTX 5060 Ti",
                "published_at": "2026-10-28T16:00:00-03:00",
            },
        ]

        prioritized = _prioritize_offers(offers, today=date(2026, 10, 28))

        self.assertEqual(
            [offer["item"] for offer in prioritized],
            [
                "Placa de vídeo RTX 5060 Ti",
                "Placa de vídeo RX 9060 XT 16GB",
                "Placa de vídeo RTX 5060",
            ],
        )

    def test_prioritizes_ti_cards_and_today_publications(self):
        offers = [
            {
                "item": "Memória DDR5",
                "published_at": "2026-10-28T19:00:00Z",
            },
            {
                "item": "Placa de vídeo RTX 5060 Ti",
                "published_at": "2026-10-28T15:00:00-03:00",
            },
            {
                "item": "Placa de vídeo RTX 5060",
                "published_at": "2026-10-28T20:00:00Z",
            },
            {
                "item": "Placa de vídeo RTX 5060 Ti",
                "published_at": "2026-10-29T01:30:00Z",
            },
        ]

        prioritized = _prioritize_offers(offers, today=date(2026, 10, 28))

        self.assertEqual(
            [offer["published_at"] for offer in prioritized],
            [
                "2026-10-29T01:30:00Z",
                "2026-10-28T15:00:00-03:00",
                "2026-10-28T20:00:00Z",
                "2026-10-28T19:00:00Z",
            ],
        )


if __name__ == "__main__":
    unittest.main()
