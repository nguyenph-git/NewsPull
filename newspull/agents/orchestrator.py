import asyncio

from ..config import load_prefs
from .. import db
from .gatherer import GathererAgent
from .digester import DigesterAgent
from .taster import TasterAgent
from ..sources.rss import RSSSource
from ..sources.hn import HackerNewsSource
from ..sources.reddit import RedditSource
from ..sources.youtube import YouTubeSource
from ..models import RankedArticle


class OrchestratorAgent:
    def _build_sources(self, prefs: dict) -> list:
        sources = []
        cfg = prefs.get("sources", {})
        for sub in cfg.get("reddit", []):
            sources.append(RedditSource(sub))
        for channel_id in cfg.get("youtube", []):
            sources.append(YouTubeSource(channel_id))
        for url in cfg.get("rss", []):
            sources.append(RSSSource(url))
        if cfg.get("hn", True):
            sources.append(HackerNewsSource())
        return sources

    async def run(self) -> tuple[int, list[str]]:
        """Run full pipeline. Returns (articles_saved, error_messages)."""
        prefs = load_prefs()
        sources = self._build_sources(prefs)

        gatherer = GathererAgent(sources)
        digester = DigesterAgent()
        taster = TasterAgent()

        raw_articles, errors = await gatherer.fetch_all()
        if not raw_articles:
            return 0, errors

        summaries = await digester.digest_all(raw_articles, prefs)
        if not summaries:
            return 0, errors

        ranked = await taster.taste_all(summaries, prefs)

        saved = 0
        for article in ranked:
            if db.save_article(article) is not None:
                saved += 1

        return saved, errors
