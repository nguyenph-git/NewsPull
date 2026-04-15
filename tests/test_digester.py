import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest

from newspull.models import RawArticle, SummarizedArticle
from newspull.agents.digester import DigesterAgent


def make_llm_response(bullets: list[str], title: str = "Test Title") -> MagicMock:
    msg = MagicMock()
    msg.content = json.dumps({"title": title, "bullets": bullets})
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_digest_returns_summarized_article():
    article = RawArticle(
        title="Original Title",
        url="https://example.com",
        source="hn",
        content="Long article content here.",
    )
    prefs = {"digester": {"style": "concise", "keypoints": 3}}

    with patch("newspull.agents.digester.ZhipuAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create.return_value = make_llm_response(
            ["Point one", "Point two", "Point three"]
        )
        agent = DigesterAgent()
        result = asyncio.run(agent.digest(article, style="concise", keypoints=3))

    assert isinstance(result, SummarizedArticle)
    assert result.url == "https://example.com"
    assert result.source == "hn"
    assert len(result.bullets) == 3


def test_digest_returns_none_on_llm_error():
    article = RawArticle(title="T", url="https://x.com", source="hn", content="body")

    with patch("newspull.agents.digester.ZhipuAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create.side_effect = Exception("API error")
        agent = DigesterAgent()
        result = asyncio.run(agent.digest(article, style="concise", keypoints=5))

    assert result is None


def test_digest_all_filters_none_results():
    articles = [
        RawArticle(title="A", url="https://a.com", source="hn", content="body a"),
        RawArticle(title="B", url="https://b.com", source="hn", content="body b"),
    ]
    prefs = {"digester": {"style": "concise", "keypoints": 3}}

    with patch("newspull.agents.digester.ZhipuAI") as MockClient:
        instance = MockClient.return_value
        # First call succeeds, second fails
        instance.chat.completions.create.side_effect = [
            make_llm_response(["p1", "p2", "p3"]),
            Exception("error"),
        ]
        agent = DigesterAgent()
        results = asyncio.run(agent.digest_all(articles, prefs))

    assert len(results) == 1
    assert results[0].url == "https://a.com"
