import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def _format_offer(offer: dict) -> str:
    price = f' — R$ {offer["price"]:.2f}' if offer["price"] is not None else ""
    return f'- {offer["item"]}: {offer["title"]}{price}\n{offer["url"]}'


def format_messages(offers: list[dict], max_length: int = 3000) -> list[str]:
    heading = "Garimpo encontrou novas ofertas:\n\n"
    messages = []
    entries = []

    for offer in offers:
        entry = _format_offer(offer)
        candidate = heading + "\n\n".join(entries + [entry])
        if entries and len(candidate) > max_length:
            messages.append(heading + "\n\n".join(entries))
            entries = [entry]
        else:
            entries.append(entry)

    if entries:
        messages.append(heading + "\n\n".join(entries))
    return messages


def send_telegram(message: str, bot_token: str, chat_id: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": message}).encode("utf-8")
    request = Request(
        url,
        data=payload,
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
        raise RuntimeError(f"Telegram não enviou a mensagem: {description}")
