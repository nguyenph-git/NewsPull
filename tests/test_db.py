import json
from datetime import datetime, UTC

import pytest

from newspull.models import RankedArticle
import newspull.db as db_module


def make_article(url="https://example.com/1", source="hn"):
    return RankedArticle(
        title="Test Article",
        url=url,
        source=source,
        bullets=["point 1", "point 2"],
        credibility_score=0.85,
        rank_score=0.80,
        cross_ref_count=0,
        fetched_at=datetime.now(UTC),
    )


def test_init_db_creates_tables(tmp_db_path):
    db_module.init_db()
    import sqlite3
    conn = sqlite3.connect(tmp_db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "articles" in tables
    assert "feed_history" in tables


def test_save_article_returns_id(tmp_db_path):
    db_module.init_db()
    article = make_article()
    article_id = db_module.save_article(article)
    assert article_id is not None
    assert article_id > 0


def test_save_duplicate_url_returns_none(tmp_db_path):
    db_module.init_db()
    article = make_article()
    db_module.save_article(article)
    result = db_module.save_article(article)
    assert result is None


def test_get_unread_articles(tmp_db_path):
    db_module.init_db()
    db_module.save_article(make_article("https://example.com/1"))
    db_module.save_article(make_article("https://example.com/2"))
    articles = db_module.get_unread_articles(limit=10)
    assert len(articles) == 2
    assert articles[0]["read"] == 0


def test_mark_articles_read(tmp_db_path):
    db_module.init_db()
    db_module.save_article(make_article("https://example.com/1"))
    articles = db_module.get_unread_articles()
    ids = [a["id"] for a in articles]
    db_module.mark_articles_read(ids)
    assert db_module.get_unread_articles() == []


def test_get_backlog_returns_oldest_first(tmp_db_path):
    db_module.init_db()
    db_module.save_article(make_article("https://example.com/1"))
    db_module.save_article(make_article("https://example.com/2"))
    backlog = db_module.get_backlog_articles(limit=10)
    assert len(backlog) == 2


def test_count_cross_refs_zero_for_new(tmp_db_path):
    db_module.init_db()
    count = db_module.count_cross_refs("https://new-url.com/article")
    assert count == 0


def test_count_cross_refs_increments(tmp_db_path):
    db_module.init_db()
    db_module.save_article(make_article("https://example.com/story", source="hn"))
    count = db_module.count_cross_refs("https://example.com/story")
    assert count == 1
