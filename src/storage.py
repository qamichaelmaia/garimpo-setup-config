import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


class OfferStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS offers (
                url TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                first_seen TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def seen_urls(self) -> set[str]:
        rows = self.connection.execute("SELECT url FROM offers").fetchall()
        return {row[0] for row in rows}

    def mark_seen(self, offers: list[dict]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.connection.executemany(
            "INSERT OR IGNORE INTO offers (url, title, first_seen) VALUES (?, ?, ?)",
            [(offer["url"], offer["title"], now) for offer in offers if offer["url"]],
        )
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        self.connection.execute("DELETE FROM offers WHERE first_seen < ?", (cutoff,))
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
