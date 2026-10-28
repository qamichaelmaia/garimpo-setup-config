import json
import unicodedata
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from uuid import uuid4


API_BASE = "https://api-web.pelando.com.br"
SITE_BASE = "https://www.pelando.com.br"
SEARCH_LIMIT = 30


def _api_get(path: str, anonymous_id: str) -> dict:
    request = Request(
        f"{API_BASE}{path}",
        headers={
            "Accept": "application/json",
            "User-Agent": "garimpo-setup/1.0",
            "x-sosho-unlogged-id": anonymous_id,
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"Pelando retornou HTTP {error.code} ao consultar ofertas."
        ) from None

    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        message = payload.get("errorMessage", "resposta inesperada da API") if isinstance(payload, dict) else "resposta inválida da API"
        raise ValueError(f"Não foi possível ler ofertas do Pelando: {message}")
    return payload["data"]


def _search_deals(query: str, anonymous_id: str) -> list[dict]:
    params = urlencode({"term": query, "limit": SEARCH_LIMIT})
    data = _api_get(f"/feed/search?{params}", anonymous_id)
    deals = data.get("deals")
    if not isinstance(deals, list):
        raise ValueError(f"Resposta de busca inválida para {query!r}.")
    return deals


def _deal_details(slug: str, anonymous_id: str) -> dict:
    data = _api_get(f"/deals/{slug}", anonymous_id)
    if not isinstance(data.get("id"), str):
        raise ValueError(f"Resposta inválida para a oferta {slug!r}.")
    return data


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _matches_item(title: str, item: dict) -> bool:
    normalized_title = _normalize(title)
    keywords = item["keywords"]
    if not any(_normalize(keyword) in normalized_title for keyword in keywords):
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


def _valid_offer(deal: dict) -> bool:
    price = deal.get("price")
    source_url = deal.get("sourceUrl")
    return (
        deal.get("kind") == "promotion"
        and deal.get("status") == "active"
        and isinstance(price, (int, float))
        and not isinstance(price, bool)
        and price > 0
        and isinstance(source_url, str)
        and urlparse(source_url).scheme in {"http", "https"}
    )


def collect_offers(items: list[dict]) -> list[dict]:
    anonymous_id = str(uuid4())
    search_cache: dict[str, list[dict]] = {}
    candidates: dict[str, tuple[dict, dict]] = {}

    for item in items:
        if not isinstance(item.get("name"), str) or not item.get("name"):
            raise ValueError("Cada item monitorado precisa ter um nome.")
        if not isinstance(item.get("query"), str) or not item["query"]:
            raise ValueError(f"O item {item['name']!r} precisa ter uma busca.")
        if not isinstance(item.get("keywords"), list) or not item["keywords"]:
            raise ValueError(f"O item {item['name']!r} precisa ter palavras-chave.")

        query = item["query"]
        if query not in search_cache:
            search_cache[query] = _search_deals(query, anonymous_id)

        for deal in search_cache[query]:
            slug = deal.get("slug")
            title = deal.get("title")
            if (
                isinstance(slug, str)
                and isinstance(title, str)
                and _valid_offer(deal)
                and _matches_item(title, item)
            ):
                candidates.setdefault(slug, (item, deal))

    offers = []
    for slug, (item, candidate) in candidates.items():
        deal = _deal_details(slug, anonymous_id)
        if not _valid_offer(deal) or not _matches_item(deal.get("title", ""), item):
            continue

        store = deal.get("store")
        offers.append(
            {
                "item": item["name"],
                "title": deal["title"],
                "price": deal["price"],
                "store": store.get("name", "") if isinstance(store, dict) else "",
                "coupon_code": deal.get("couponCode"),
                "image_url": deal.get("imageUrl"),
                "buy_url": deal.get("sourceUrl") or candidate["sourceUrl"],
                "url": f"{SITE_BASE}/d/{slug}",
                "source": "pelando",
            }
        )

    return offers
