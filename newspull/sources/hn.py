import httpx

from .base import Source
from ..models import RawArticle

HN_API = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30"


class HackerNewsSource(Source):
    @property
    def name(self) -> str:
        return "hackernews"

    def fetch(self) -> list[RawArticle]:
        try:
            response = httpx.get(HN_API, timeout=10)
            response.raise_for_status()
            data = response.json()
            articles = []
            for hit in data.get("hits", []):
                url = hit.get("url", "")
                if not url:
                    continue
                content = hit.get("story_text") or f"Points: {hit.get('points', 0)}, Comments: {hit.get('num_comments', 0)}"
                articles.append(
                    RawArticle(
                        title=hit.get("title", "Untitled"),
                        url=url,
                        source="hackernews",
                        content=content[:4000],
                    )
                )
            return articles
        except Exception:
            return []
