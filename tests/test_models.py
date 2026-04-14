from datetime import datetime
from newspull.models import RawArticle, SummarizedArticle, RankedArticle


def test_raw_article_fields():
    a = RawArticle(title="T", url="https://x.com", source="hn", content="body")
    assert a.title == "T"
    assert a.url == "https://x.com"
    assert a.source == "hn"
    assert a.content == "body"


def test_summarized_article_fields():
    a = SummarizedArticle(
        title="T", url="https://x.com", source="hn", bullets=["point 1", "point 2"]
    )
    assert len(a.bullets) == 2


def test_ranked_article_has_scores():
    a = RankedArticle(
        title="T",
        url="https://x.com",
        source="hn",
        bullets=["p1"],
        credibility_score=0.9,
        rank_score=0.85,
        cross_ref_count=2,
        fetched_at=datetime.utcnow(),
    )
    assert a.credibility_score == 0.9
    assert a.rank_score == 0.85
    assert a.cross_ref_count == 2
