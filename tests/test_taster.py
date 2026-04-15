import asyncio

import pytest

from newspull.models import SummarizedArticle, RankedArticle
from newspull.agents.taster import TasterAgent


def make_summary(url="https://x.com/story", source="hackernews", title="AI News Today"):
    return SummarizedArticle(
        title=title,
        url=url,
        source=source,
        bullets=["AI is advancing rapidly", "New model released by researchers"],
    )


DEFAULT_PREFS = {
    "topics": {"ai": 1.0, "tech": 0.8, "politics": 0.3},
    "credibility": {"min_score": 0.5, "cross_ref_bonus": 0.2},
}


def test_taste_returns_ranked_article(tmp_db_path):
    import newspull.db as db
    db.init_db()

    agent = TasterAgent()
    result = asyncio.run(agent.taste(make_summary(), DEFAULT_PREFS))

    assert isinstance(result, RankedArticle)
    assert 0.0 <= result.credibility_score <= 1.0
    assert 0.0 <= result.rank_score <= 1.0
    assert result.cross_ref_count == 0


def test_taste_filters_low_credibility(tmp_db_path):
    import newspull.db as db
    db.init_db()

    prefs = {
        "topics": {"ai": 1.0},
        "credibility": {"min_score": 0.99, "cross_ref_bonus": 0.0},
    }
    # unknown source gets low reputation
    agent = TasterAgent()
    result = asyncio.run(agent.taste(make_summary(source="unknown_source"), prefs))
    assert result is None


def test_taste_boosts_matching_topic(tmp_db_path):
    import newspull.db as db
    db.init_db()

    agent = TasterAgent()
    ai_article = make_summary(title="New AI Model Released Today")
    politics_article = make_summary(title="Election Results Come In", url="https://x.com/election")

    ai_result = asyncio.run(agent.taste(ai_article, DEFAULT_PREFS))
    pol_result = asyncio.run(agent.taste(politics_article, DEFAULT_PREFS))

    assert ai_result is not None
    assert pol_result is not None
    assert ai_result.rank_score >= pol_result.rank_score


def test_taste_all_processes_batch(tmp_db_path):
    import newspull.db as db
    db.init_db()

    articles = [
        make_summary(url="https://x.com/1"),
        make_summary(url="https://x.com/2"),
        make_summary(url="https://x.com/3"),
    ]
    agent = TasterAgent()
    results = asyncio.run(agent.taste_all(articles, DEFAULT_PREFS))
    assert len(results) >= 1
    assert all(isinstance(r, RankedArticle) for r in results)
