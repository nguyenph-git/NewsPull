import asyncio

from ..sources.base import Source
from ..models import RawArticle


class GathererAgent:
    def __init__(self, sources: list[Source]):
        self.sources = sources

    async def fetch_all(self) -> tuple[list[RawArticle], list[str]]:
        """Fetch from all sources in parallel. Returns (articles, error_messages)."""
        if not self.sources:
            return [], []

        tasks = [self._fetch_source(s) for s in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles: list[RawArticle] = []
        errors: list[str] = []
        for source, result in zip(self.sources, results):
            if isinstance(result, Exception):
                errors.append(f"{source.name}: {result}")
            else:
                articles.extend(result)

        return articles, errors

    async def _fetch_source(self, source: Source) -> list[RawArticle]:
        return await asyncio.to_thread(source.fetch)
