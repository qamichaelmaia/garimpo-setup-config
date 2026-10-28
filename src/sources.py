import re
from urllib.parse import quote_plus

import feedparser


def _parse_price(text: str):
    if not text:
        return None
    m = re.search(r"R\$\s*([0-9\.]+,[0-9]{2})", text)
    if not m:
        return None
    num = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(num)
    except ValueError:
        return None


def _google_shopping_rss(query: str, country: str = "BR", lang: str = "pt-BR"):
    q = quote_plus(query)
    url = f"https://news.google.com/rss/search?q={q}+when:7d&hl={lang}&gl={country}&ceid={country}:{lang}"
    feed = feedparser.parse(url)
    offers = []
    for e in feed.entries:
        title = getattr(e, "title", "")
        link = getattr(e, "link", "")
        summary = getattr(e, "summary", "")
        offers.append(
            {
                "title": title,
                "url": link,
                "store": "google-news",
                "price": _parse_price(f"{title} {summary}"),
                "source": "google-news-rss",
            }
        )
    return offers


def _buscape_rss(query: str):
    q = quote_plus(query)
    url = f"https://www.buscape.com.br/busca/{q}"
    return [
        {
            "title": f"Busca Buscapé: {query}",
            "url": url,
            "store": "buscape",
            "price": None,
            "source": "buscape-link",
        }
    ]


def collect_offers(items: list[dict]) -> list[dict]:
    offers = []
    for item in items:
        query = item["keywords"][0]
        offers.extend(_google_shopping_rss(query))
        offers.extend(_buscape_rss(query))
    return offers
