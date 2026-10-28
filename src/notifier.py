import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def _format_price(price: float) -> str:
    return f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_offer(offer: dict) -> str:
    lines = [
        f'🛒 {offer["title"]}',
        f'🏪 Loja: {offer["store"]}' if offer.get("store") else None,
        f'✅ Por: R$ {_format_price(offer["price"])}',
        f'🎟️ Cupom: {offer["coupon_code"]}' if offer.get("coupon_code") else None,
        f'👉 Ver oferta e acessar a loja: {offer["url"]}',
        "⚠️ Preço e estoque podem mudar; confira as condições na loja.",
    ]
    return "\n".join(line for line in lines if line)


def send_telegram_offer(offer: dict, bot_token: str, chat_id: str) -> None:
    caption = format_offer(offer)
    send_photo = bool(offer.get("image_url")) and len(caption) <= 1024
    method = "sendPhoto" if send_photo else "sendMessage"
    payload = {"chat_id": chat_id}
    if send_photo:
        payload.update({"photo": offer["image_url"], "caption": caption})
    else:
        payload["text"] = caption

    request = Request(
        f"https://api.telegram.org/bot{bot_token}/{method}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "garimpo-setup/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"Telegram retornou HTTP {error.code}") from None

    if not result.get("ok"):
        description = result.get("description", "erro não especificado")
        raise RuntimeError(f"Telegram não enviou a oferta: {description}")
