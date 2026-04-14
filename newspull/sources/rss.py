import httpx
import feedparser

from .base import Source
from ..models import RawArticle


class RSSSource(Source):
    def __init__(self, url: str):
        self._url = url

    @property
    def name(self) -> str:
        return f"rss:{self._url}"

    def fetch(self) -> list[RawArticle]:
        try:
            response = httpx.get(self._url, timeout=10, follow_redirects=True)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            articles = []
            for entry in feed.entries:
                url = entry.get("link", "")
                if not url:
                    continue
                content = entry.get("summary", "") or entry.get("description", "")
                articles.append(
                    RawArticle(
                        title=entry.get("title", "Untitled"),
                        url=url,
                        source="rss",
                        content=content[:4000],
                    )
                )
            return articles
        except Exception:
            return []
