from unittest.mock import patch, MagicMock
import pytest

from newspull.models import RawArticle
from newspull.sources.rss import RSSSource
from newspull.sources.hn import HackerNewsSource


FAKE_FEED_XML = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Article One</title>
      <link>https://example.com/one</link>
      <description>First article body text here.</description>
    </item>
    <item>
      <title>Article Two</title>
      <link>https://example.com/two</link>
      <description>Second article body text here.</description>
    </item>
  </channel>
</rss>"""

FAKE_HN_RESPONSE = {
    "hits": [
        {
            "title": "HN Article One",
            "url": "https://hn.example.com/one",
            "story_text": "Some HN discussion text.",
            "num_comments": 42,
            "points": 300,
        },
        {
            "title": "HN Article Two",
            "url": "https://hn.example.com/two",
            "story_text": None,
            "num_comments": 10,
            "points": 100,
        },
    ]
}


def test_rss_source_returns_raw_articles():
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = FAKE_FEED_XML
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        source = RSSSource("https://example.com/feed.xml")
        articles = source.fetch()

    assert len(articles) == 2
    assert all(isinstance(a, RawArticle) for a in articles)
    assert articles[0].title == "Article One"
    assert articles[0].url == "https://example.com/one"
    assert articles[0].source == "rss"


def test_rss_source_skips_items_without_link():
    no_link_xml = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item><title>No Link</title><description>body</description></item>
</channel></rss>"""
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = no_link_xml
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        source = RSSSource("https://example.com/feed.xml")
        articles = source.fetch()

    assert articles == []


def test_rss_source_returns_empty_on_http_error():
    with patch("httpx.get") as mock_get:
        mock_get.side_effect = Exception("timeout")
        source = RSSSource("https://example.com/feed.xml")
        articles = source.fetch()
    assert articles == []


def test_hn_source_returns_raw_articles():
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = FAKE_HN_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        source = HackerNewsSource()
        articles = source.fetch()

    assert len(articles) == 2
    assert articles[0].title == "HN Article One"
    assert articles[0].source == "hackernews"


def test_hn_source_returns_empty_on_error():
    with patch("httpx.get") as mock_get:
        mock_get.side_effect = Exception("network error")
        source = HackerNewsSource()
        articles = source.fetch()
    assert articles == []
