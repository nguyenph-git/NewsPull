import httpx

from .base import Source
from ..models import RawArticle


class RedditSource(Source):
    def __init__(self, subreddit: str):
        # normalise: strip leading "r/" if present
        self._sub = subreddit.lstrip("r/")

    @property
    def name(self) -> str:
        return f"reddit:r/{self._sub}"

    def fetch(self) -> list[RawArticle]:
        url = f"https://www.reddit.com/r/{self._sub}/top.json?limit=25&t=day"
        headers = {"User-Agent": "newspull/0.1"}
        try:
            response = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
            response.raise_for_status()
            data = response.json()
            articles = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                post_url = post.get("url", "")
                if not post_url:
                    continue
                content = post.get("selftext", "") or f"Score: {post.get('score', 0)}"
                articles.append(
                    RawArticle(
                        title=post.get("title", "Untitled"),
                        url=post_url,
                        source="reddit",
                        content=content[:4000],
                    )
                )
            return articles
        except Exception:
            return []
