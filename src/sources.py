import json
import re
import unicodedata
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


PROMOBIT_API_BASE = "https://api.promobit.com.br"
PROMOBIT_SITE_BASE = "https://www.promobit.com.br"
PROMOBIT_IMAGE_BASE = "https://i.promobit.com.br/268"
BILOMETRO_API_BASE = "https://bilometro-api-583495244408.us-east1.run.app"
BILOMETRO_PAGE_LIMIT = 100


def _search_offers(query: str) -> list[dict]:
    url = f"{PROMOBIT_API_BASE}/search?{urlencode({'q': query})}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Referer": f"{PROMOBIT_SITE_BASE}/",
            "User-Agent": "garimpo-setup/1.0",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"Promobit retornou HTTP {error.code} ao consultar ofertas."
        ) from None

    offers = payload.get("active_offers") if isinstance(payload, dict) else None
    if not isinstance(offers, list):
        raise ValueError(f"Resposta de busca inválida do Promobit para {query!r}.")
    return offers


def _search_bilometro_promotions() -> list[dict]:
    params = urlencode(
        {
            "page": 1,
            "limit": BILOMETRO_PAGE_LIMIT,
            "includeEmptyGames": "false",
            "from": "bilometro",
        }
    )
    request = Request(
        f"{BILOMETRO_API_BASE}/promotions?{params}",
        headers={
            "Accept": "application/json",
            "User-Agent": "garimpo-setup/1.0",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"Bilômetro retornou HTTP {error.code} ao consultar promoções."
        ) from None

    promotions = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(promotions, list):
        raise ValueError("Resposta de promoções inválida do Bilômetro.")
    return promotions


def _parse_price(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"R\$\s*([\d.]+(?:,\d{2})?)", text, re.IGNORECASE)
    if not match:
        return None
    number = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(number)
    except ValueError:
        return None


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(re.sub(r"[^a-z0-9]+", " ", plain).split())


def _matches_item(title: str, item: dict) -> bool:
    normalized_title = _normalize(title)
    if not any(
        _normalize(keyword) in normalized_title for keyword in item["keywords"]
    ):
        return False
    if not all(
        _normalize(keyword) in normalized_title
        for keyword in item.get("required_keywords", [])
    ):
        return False
    return not any(
        _normalize(keyword) in normalized_title
        for keyword in item.get("exclude_keywords", [])
    )


def _is_active_offer(offer: dict) -> bool:
    price = offer.get("offer_price")
    return (
        isinstance(offer.get("offer_title"), str)
        and isinstance(offer.get("offer_slug"), str)
        and isinstance(price, (int, float))
        and not isinstance(price, bool)
        and price > 0
        and isinstance(offer.get("store_name"), str)
        and bool(offer["store_name"])
    )


def _image_url(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith(("http://", "https://")):
        return path
    return f"{PROMOBIT_IMAGE_BASE}/{path.lstrip('/')}"


def collect_offers(items: list[dict]) -> list[dict]:
    search_cache: dict[str, list[dict]] = {}
    candidates: dict[str, tuple[dict, dict]] = {}
    promotions = _search_bilometro_promotions()

    for item in items:
        if not isinstance(item.get("name"), str) or not item["name"]:
            raise ValueError("Cada item monitorado precisa ter um nome.")
        if not isinstance(item.get("query"), str) or not item["query"]:
            raise ValueError(f"O item {item['name']!r} precisa ter uma busca.")
        if not isinstance(item.get("keywords"), list) or not item["keywords"]:
            raise ValueError(f"O item {item['name']!r} precisa ter palavras-chave.")

        query = item["query"]
        if query not in search_cache:
            search_cache[query] = _search_offers(query)

        for offer in search_cache[query]:
            title = offer.get("offer_title")
            slug = offer.get("offer_slug")
            if (
                isinstance(title, str)
                and isinstance(slug, str)
                and _is_active_offer(offer)
                and _matches_item(title, item)
            ):
                candidates.setdefault(slug, (item, offer))

    results = []
    for slug, (item, offer) in candidates.items():
        offer_url = f"{PROMOBIT_SITE_BASE}/oferta/{slug}/"
        image_path = offer.get("offer_photo")
        results.append(
            {
                "item": item["name"],
                "title": offer["offer_title"],
                "price": offer["offer_price"],
                "store": offer["store_name"],
                "coupon_code": offer.get("offer_coupon"),
                "image_url": _image_url(image_path) if isinstance(image_path, str) else None,
                "url": offer_url,
                "source": "promobit",
            }
        )

    for item in items:
        for promotion in promotions:
            title = promotion.get("gameName")
            purchase_url = promotion.get("purchaseLink")
            price = _parse_price(promotion.get("priceDetails"))
            if (
                not isinstance(title, str)
                or not isinstance(purchase_url, str)
                or urlparse(purchase_url).scheme not in {"http", "https"}
                or promotion.get("status") != "SENT"
                or price is None
                or not _matches_item(title, item)
            ):
                continue

            results.append(
                {
                    "item": item["name"],
                    "title": title,
                    "price": price,
                    "store": promotion.get("storeName", ""),
                    "coupon_code": promotion.get("couponCode"),
                    "image_url": promotion.get("imageUrl"),
                    "url": purchase_url,
                    "source": "bilometro",
                }
            )

    unique_offers = {}
    for offer in results:
        unique_offers.setdefault(offer["url"], offer)
    results = list(unique_offers.values())

    return results
