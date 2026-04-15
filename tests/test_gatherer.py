import asyncio
import pytest
from unittest.mock import MagicMock

from newspull.models import RawArticle
from newspull.agents.gatherer import GathererAgent
from newspull.sources.base import Source


class GoodSource(Source):
    @property
    def name(self):
        return "good"

    def fetch(self):
        return [RawArticle(title="A", url="https://a.com", source="good", content="body")]


class FailingSource(Source):
    @property
    def name(self):
        return "bad"

    def fetch(self):
        raise RuntimeError("network timeout")


def test_fetch_all_combines_results():
    agent = GathererAgent([GoodSource(), GoodSource()])
    articles, errors = asyncio.run(agent.fetch_all())
    assert len(articles) == 2
    assert errors == []


def test_fetch_all_skips_failed_source():
    agent = GathererAgent([GoodSource(), FailingSource()])
    articles, errors = asyncio.run(agent.fetch_all())
    assert len(articles) == 1
    assert len(errors) == 1
    assert "bad" in errors[0]


def test_fetch_all_returns_empty_when_all_fail():
    agent = GathererAgent([FailingSource()])
    articles, errors = asyncio.run(agent.fetch_all())
    assert articles == []
    assert len(errors) == 1


def test_fetch_all_empty_sources():
    agent = GathererAgent([])
    articles, errors = asyncio.run(agent.fetch_all())
    assert articles == []
    assert errors == []
