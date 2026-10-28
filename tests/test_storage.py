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


if __name__ == "__main__":
    unittest.main()
