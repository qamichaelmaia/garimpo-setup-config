import io
import json
import unittest
from unittest.mock import patch

from src.notifier import format_messages, send_telegram


class FormatMessagesTests(unittest.TestCase):
    def test_formats_price_and_link(self):
        messages = format_messages(
            [
                {
                    "item": "GPU",
                    "title": "Oferta",
                    "price": 2999.9,
                    "url": "https://example.com/oferta",
                }
            ]
        )

        self.assertEqual(len(messages), 1)
        self.assertIn("R$ 2999.90", messages[0])
        self.assertIn("https://example.com/oferta", messages[0])

    def test_splits_messages_without_dropping_heading(self):
        offers = [
            {
                "item": "GPU",
                "title": f"Oferta {index}",
                "price": None,
                "url": f"https://example.com/{index}",
            }
            for index in range(3)
        ]

        messages = format_messages(offers, max_length=100)

        self.assertGreater(len(messages), 1)
        self.assertTrue(all(message.startswith("Garimpo encontrou") for message in messages))
        self.assertEqual(sum(message.count("https://example.com/") for message in messages), 3)


class SendTelegramTests(unittest.TestCase):
    @patch("src.notifier.urlopen")
    def test_sends_message_to_telegram(self, urlopen):
        response = io.BytesIO(b'{"ok": true}')
        response.status = 200
        urlopen.return_value.__enter__.return_value = response

        send_telegram("Oferta de teste", "bot-token", "123")

        request = urlopen.call_args.args[0]
        self.assertIn("/botbot-token/sendMessage", request.full_url)
        self.assertEqual(
            json.loads(request.data),
            {"chat_id": "123", "text": "Oferta de teste"},
        )

    @patch("src.notifier.urlopen")
    def test_raises_when_telegram_rejects_message(self, urlopen):
        response = io.BytesIO(
            b'{"ok": false, "description": "chat not found"}'
        )
        response.status = 200
        urlopen.return_value.__enter__.return_value = response

        with self.assertRaisesRegex(RuntimeError, "chat not found"):
            send_telegram("Oferta de teste", "bot-token", "123")


if __name__ == "__main__":
    unittest.main()
