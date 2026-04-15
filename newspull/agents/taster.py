import asyncio

from ..models import SummarizedArticle, RankedArticle
from .. import db

SOURCE_REPUTATION: dict[str, float] = {
    "hackernews": 0.9,
    "reddit": 0.7,
    "youtube": 0.65,
    "rss": 0.75,
}
DEFAULT_REPUTATION = 0.6


class TasterAgent:
    def _credibility_score(
        self, article: SummarizedArticle, cross_ref_bonus: float
    ) -> tuple[float, int]:
        base = SOURCE_REPUTATION.get(article.source.lower(), DEFAULT_REPUTATION)
        cross_ref_count = db.count_cross_refs(article.url)
        score = min(1.0, base + cross_ref_bonus * cross_ref_count)
        return round(score, 3), cross_ref_count

    def _rank_score(
        self, credibility: float, article: SummarizedArticle, topic_weights: dict
    ) -> float:
        text = (article.title + " " + " ".join(article.bullets)).lower()
        weight = max(
            (v for k, v in topic_weights.items() if k.lower() in text),
            default=0.5,
        )
        return round(credibility * weight, 3)

    async def taste(
        self, article: SummarizedArticle, prefs: dict
    ) -> RankedArticle | None:
        min_score = prefs.get("credibility", {}).get("min_score", 0.5)
        cross_ref_bonus = prefs.get("credibility", {}).get("cross_ref_bonus", 0.2)
        topic_weights = prefs.get("topics", {})

        credibility, cross_ref_count = self._credibility_score(article, cross_ref_bonus)
        if credibility < min_score:
            return None

        rank = self._rank_score(credibility, article, topic_weights)
        return RankedArticle(
            title=article.title,
            url=article.url,
            source=article.source,
            bullets=article.bullets,
            credibility_score=credibility,
            rank_score=rank,
            cross_ref_count=cross_ref_count,
        )

    async def taste_all(
        self, articles: list[SummarizedArticle], prefs: dict
    ) -> list[RankedArticle]:
        tasks = [self.taste(a, prefs) for a in articles]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
