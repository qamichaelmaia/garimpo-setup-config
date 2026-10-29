import tempfile
import unittest
from pathlib import Path

from src.storage import OfferStore


class OfferStoreTests(unittest.TestCase):
    def test_records_seen_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            store = OfferStore(str(Path(directory) / "offers.sqlite3"))
            store.mark_seen(
                [{"url": "https://example.com/offer", "title": "Oferta de teste"}]
            )

            self.assertEqual(store.seen_urls(), {"https://example.com/offer"})
            store.close()

    def test_records_mega_discount_alerts_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            store = OfferStore(str(Path(directory) / "offers.sqlite3"))
            offer = {
                "url": "https://example.com/offer",
                "title": "Oferta de teste",
            }

            store.mark_seen([offer])
            self.assertEqual(store.seen_mega_discount_urls(), set())

            store.mark_mega_discount_seen([offer])

            self.assertEqual(
                store.seen_mega_discount_urls(), {"https://example.com/offer"}
            )
            store.close()


if __name__ == "__main__":
    unittest.main()
