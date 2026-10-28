import re
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import feedparser


def _parse_price(text: str) -> float | None:
    if not text:
        return None
    m = re.search(r"R\$\s*([\d.]+,\d{2})", text, re.IGNORECASE)
    if not m:
        return None
    num = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(num)
    except ValueError:
        return None


def _google_news_rss(
    query: str, country: str = "BR", lang: str = "pt-BR"
) -> list[dict]:
    q = quote_plus(query)
    url = f"https://news.google.com/rss/search?q={q}+when:7d&hl={lang}&gl={country}&ceid={country}:{lang}"
    request = Request(url, headers={"User-Agent": "garimpo-setup/1.0"})
    with urlopen(request, timeout=20) as response:
        feed = feedparser.parse(response.read())

    if feed.bozo and not feed.entries:
        raise ValueError(f"Feed RSS inválido para a busca {query!r}") from feed.bozo_exception

    offers = []
    for e in feed.entries:
        title = getattr(e, "title", "")
        link = getattr(e, "link", "")
        summary = getattr(e, "summary", "")
        summary_text = re.sub(r"<[^>]+>", " ", summary)
        offers.append(
            {
                "title": title,
                "url": link,
                "store": "google-news",
                "price": _parse_price(f"{title} {summary_text}"),
                "source": "google-news-rss",
                "query": query,
            }
        )
    return offers


def collect_offers(items: list[dict]) -> list[dict]:
    offers = []
    for item in items:
        for query in item["keywords"]:
            for offer in _google_news_rss(query):
                offer["item"] = item["name"]
                offers.append(offer)

    unique_offers = {}
    for offer in offers:
        key = offer["url"] or f'{offer["title"]}|{offer["query"]}'
        unique_offers[key] = offer
    return list(unique_offers.values())
