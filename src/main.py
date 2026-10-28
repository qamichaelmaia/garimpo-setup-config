import json
import logging
import os
import sys
from pathlib import Path

from src.notifier import format_offer, send_telegram_offer
from src.sources import collect_offers
from src.storage import OfferStore


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ITEMS_PATH = ROOT / "config" / "items.json"
DEFAULT_DB_PATH = ROOT / ".state" / "garimpo.sqlite3"


def main() -> int:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    items_path = Path(os.getenv("GARIMPO_ITEMS_PATH", str(DEFAULT_ITEMS_PATH)))
    db_path = os.getenv("GARIMPO_DB_PATH", str(DEFAULT_DB_PATH))

    with items_path.open(encoding="utf-8") as file:
        items = json.load(file)
    if not isinstance(items, list) or not items:
        raise ValueError(f"A configuração {items_path} precisa conter uma lista de itens.")

    offers = collect_offers(items)
    store = OfferStore(db_path)
    try:
        known_urls = store.seen_urls()
        new_offers = [offer for offer in offers if offer["url"] not in known_urls]
        logging.info(
            "Coleta finalizada: %d resultados, %d novos.",
            len(offers),
            len(new_offers),
        )

        if not new_offers:
            return 0

        if os.getenv("GARIMPO_DRY_RUN", "").lower() in {"1", "true", "yes"}:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            for offer in new_offers:
                print(format_offer(offer))
                print()
            return 0

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not bot_token or not chat_id:
            raise ValueError(
                "Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID antes de enviar alertas."
            )

        for offer in new_offers:
            send_telegram_offer(offer, bot_token, chat_id)
            store.mark_seen([offer])
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logging.exception("Falha na execução do garimpo.")
        sys.exit(1)
