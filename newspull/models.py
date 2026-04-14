from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class RawArticle:
    title: str
    url: str
    source: str
    content: str


@dataclass
class SummarizedArticle:
    title: str
    url: str
    source: str
    bullets: list[str]


@dataclass
class RankedArticle:
    title: str
    url: str
    source: str
    bullets: list[str]
    credibility_score: float
    rank_score: float
    cross_ref_count: int
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))
