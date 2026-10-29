import io
import json
import unittest
from unittest.mock import patch

from src.notifier import format_offer, send_telegram_offer


class TelegramOfferTests(unittest.TestCase):
    def setUp(self):
        self.offer = {
            "title": "Placa de Vídeo RTX 5060",
            "store": "Loja Exemplo",
            "price": 2499.9,
            "coupon_code": "GPU10",
            "image_url": "https://store.example/gpu.jpg",
            "url": "https://www.promobit.com.br/oferta/rtx-5060/",
            "source": "promobit",
        }

    def test_formats_offer_details_in_brazilian_currency(self):
        message = format_offer(self.offer)

        self.assertIn("R$ 2.499,90", message)
        self.assertIn("Cupom: GPU10", message)
        self.assertIn("Loja: Loja Exemplo", message)
        self.assertIn(self.offer["url"], message)
        self.assertIn("Fonte: Promobit", message)

    def test_formats_old_and_current_prices_and_mega_discount(self):
        offer = {
            **self.offer,
            "old_price": 3299.9,
            "price": 2699.9,
            "mega_discount_threshold": 2700,
        }

        message = format_offer(offer)

        self.assertIn("🔥 MEGA DESCONTO 🔥", message)
        self.assertIn("De: R$ 3.299,90", message)
        self.assertIn("Por: R$ 2.699,90", message)

    def test_does_not_mark_price_equal_to_threshold_as_mega_discount(self):
        offer = {**self.offer, "price": 2700, "mega_discount_threshold": 2700}

        self.assertNotIn("MEGA DESCONTO", format_offer(offer))

    def test_does_not_show_old_price_when_it_is_not_higher(self):
        offer = {**self.offer, "old_price": 2000}

        self.assertNotIn("De: R$", format_offer(offer))

    @patch("src.notifier.urlopen")
    def test_sends_offer_with_product_image(self, urlopen):
        response = io.BytesIO(b'{"ok": true}')
        urlopen.return_value.__enter__.return_value = response

        send_telegram_offer(self.offer, "bot-token", "123")

        request = urlopen.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/sendPhoto"))
        payload = json.loads(request.data)
        self.assertEqual(payload["chat_id"], "123")
        self.assertEqual(payload["photo"], self.offer["image_url"])
        self.assertIn("R$ 2.499,90", payload["caption"])

    @patch("src.notifier.urlopen")
    def test_sends_text_when_offer_has_no_image(self, urlopen):
        response = io.BytesIO(b'{"ok": true}')
        urlopen.return_value.__enter__.return_value = response
        offer = {**self.offer, "image_url": None}

        send_telegram_offer(offer, "bot-token", "123")

        request = urlopen.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/sendMessage"))
        self.assertIn("text", json.loads(request.data))

    @patch("src.notifier.urlopen")
    def test_raises_when_telegram_rejects_offer(self, urlopen):
        response = io.BytesIO(
            b'{"ok": false, "description": "chat not found"}'
        )
        urlopen.return_value.__enter__.return_value = response

        with self.assertRaisesRegex(RuntimeError, "chat not found"):
            send_telegram_offer(self.offer, "bot-token", "123")


if __name__ == "__main__":
    unittest.main()
