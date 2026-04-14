# NewsPull Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 5-agent AGNO news aggregation CLI (+ web view) that fetches, summarises, scores, and ranks stories from multiple sources using GLM models, adapting to natural-language user feedback.

**Architecture:** Five async Python agents (Orchestrator, Gatherer, Digester, Taster, Feedback) form a parallel in-memory pipeline: Gatherers fetch raw articles from sources simultaneously, Digesters summarise in parallel via GLM-4-Flash, Tasters score credibility and apply preferences in parallel via GLM-4-Air, and the Orchestrator persists ranked results to SQLite. The CLI and web view read from SQLite on demand.

**Tech Stack:** Python 3.11+, AGNO, zhipuai SDK (GLM-4-Flash + GLM-4-Air), httpx, feedparser, playwright, typer, rich, Flask + HTMX, sqlite3 (stdlib), tomllib/tomli-w, pytest

---

## File Map

```
newspull/
├── __init__.py
├── models.py                  # RawArticle, SummarizedArticle, RankedArticle dataclasses
├── db.py                      # SQLite schema, init, CRUD (save_article, get_unread, get_backlog, mark_read, count_cross_refs)
├── config.py                  # load_prefs(), save_prefs() — ~/.newspull/preferences.toml
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py        # OrchestratorAgent.run() — async pipeline coordinator
│   ├── gatherer.py            # GathererAgent.fetch_all() — parallel source dispatch
│   ├── digester.py            # DigesterAgent.digest_all() — GLM-4-Flash batch summarisation
│   ├── taster.py              # TasterAgent.taste_all() — credibility + preference ranking
│   └── feedback.py            # FeedbackAgent.process(text) — GLM-4-Air prefs update
├── sources/
│   ├── __init__.py
│   ├── base.py                # Source ABC: name: str, fetch() -> list[RawArticle]
│   ├── rss.py                 # RSSSource(url) — httpx + feedparser
│   ├── hn.py                  # HackerNewsSource() — httpx Algolia HN API
│   ├── reddit.py              # RedditSource(subreddit) — httpx reddit .json API
│   └── youtube.py             # YouTubeSource(channel_id) — httpx YouTube RSS feed
├── cli/
│   ├── __init__.py
│   └── main.py                # typer app: newspull / pull / fetch / feedback / web / config
└── web/
    ├── __init__.py
    ├── app.py                 # Flask: GET / · POST /review · POST /fetch · POST /mark-read
    └── templates/
        └── index.html         # HTMX feed + review box

tests/
├── conftest.py                # tmp_db_path, sample_raw_article, sample_ranked_article, tmp_prefs fixtures
├── test_models.py
├── test_db.py
├── test_config.py
├── test_sources.py            # httpx mock for all 4 sources
├── test_digester.py           # zhipuai mock
├── test_taster.py             # credibility scoring, preference ranking
├── test_orchestrator.py       # full pipeline with mocked sources + LLM
├── test_feedback.py           # zhipuai mock + prefs update
├── test_cli.py                # typer CliRunner
└── test_web.py                # Flask test client

pyproject.toml
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `newspull/__init__.py`
- Create: `newspull/agents/__init__.py`
- Create: `newspull/sources/__init__.py`
- Create: `newspull/cli/__init__.py`
- Create: `newspull/web/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "newspull"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "agno>=1.0",
    "zhipuai>=2.1",
    "httpx>=0.27",
    "feedparser>=6.0",
    "playwright>=1.44",
    "typer>=0.12",
    "rich>=13.0",
    "flask>=3.0",
    "tomli-w>=1.0",
]

[project.scripts]
newspull = "newspull.cli.main:app"

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23"]
```

- [ ] **Step 2: Create all `__init__.py` files and directory structure**

```bash
mkdir -p newspull/agents newspull/sources newspull/cli newspull/web/templates tests
touch newspull/__init__.py newspull/agents/__init__.py newspull/sources/__init__.py
touch newspull/cli/__init__.py newspull/web/__init__.py tests/__init__.py
```

- [ ] **Step 3: Write `tests/conftest.py`**

```python
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from newspull.models import RawArticle, RankedArticle


@pytest.fixture
def tmp_db_path(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    import newspull.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return db_path


@pytest.fixture
def tmp_prefs_path(tmp_path, monkeypatch):
    prefs_path = tmp_path / "preferences.toml"
    import newspull.config as config_module
    monkeypatch.setattr(config_module, "PREFS_PATH", prefs_path)
    return prefs_path


@pytest.fixture
def sample_raw_article():
    return RawArticle(
        title="GLM-5 Announced With Major Improvements",
        url="https://example.com/glm5",
        source="hackernews",
        content="Zhipu AI has announced GLM-5 with significant improvements in reasoning and code generation. The model outperforms previous versions on standard benchmarks.",
    )


@pytest.fixture
def sample_ranked_article():
    return RankedArticle(
        title="GLM-5 Announced With Major Improvements",
        url="https://example.com/glm5",
        source="hackernews",
        bullets=["Zhipu AI released GLM-5", "Improved reasoning and code gen", "Beats benchmarks"],
        credibility_score=0.9,
        rank_score=0.85,
        cross_ref_count=0,
        fetched_at=datetime.utcnow(),
    )


@pytest.fixture
def default_prefs():
    return {
        "topics": {"ai": 1.0, "tech": 0.8, "politics": 0.3},
        "sources": {
            "reddit": ["r/MachineLearning"],
            "youtube": [],
            "rss": [],
            "hn": True,
        },
        "credibility": {"min_score": 0.5, "cross_ref_bonus": 0.2},
        "digester": {"style": "concise", "keypoints": 5},
    }
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -e ".[dev]"
```

Expected: No errors. `newspull --help` fails (no commands yet) but package is importable.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml newspull/ tests/
git commit -m "chore: project scaffolding — package structure and dependencies"
```

---

## Task 2: Models

**Files:**
- Create: `newspull/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_models.py -v
```

Expected: `ImportError: cannot import name 'RawArticle' from 'newspull.models'`

- [ ] **Step 3: Write `newspull/models.py`**

```python
from dataclasses import dataclass, field
from datetime import datetime


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
    fetched_at: datetime = field(default_factory=datetime.utcnow)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_models.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add newspull/models.py tests/test_models.py
git commit -m "feat: add RawArticle, SummarizedArticle, RankedArticle models"
```

---

## Task 3: Database Layer

**Files:**
- Create: `newspull/db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_db.py
import json
from datetime import datetime

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
        fetched_at=datetime.utcnow(),
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_db.py -v
```

Expected: `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Write `newspull/db.py`**

```python
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import RankedArticle

DB_PATH = Path.home() / ".newspull" / "newspull.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            bullet_summary TEXT NOT NULL,
            credibility_score REAL NOT NULL,
            rank_score REAL NOT NULL,
            cross_ref_count INTEGER NOT NULL DEFAULT 0,
            fetched_at TEXT NOT NULL,
            read INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS feed_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            article_id INTEGER NOT NULL,
            shown_at TEXT NOT NULL,
            FOREIGN KEY (article_id) REFERENCES articles(id)
        );
    """)
    conn.commit()
    conn.close()


def save_article(article: RankedArticle) -> int | None:
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO articles
               (source, url, title, bullet_summary, credibility_score,
                rank_score, cross_ref_count, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                article.source,
                article.url,
                article.title,
                json.dumps(article.bullets),
                article.credibility_score,
                article.rank_score,
                article.cross_ref_count,
                article.fetched_at.isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid if cursor.rowcount > 0 else None
    finally:
        conn.close()


def get_unread_articles(limit: int = 20) -> list[dict]:
    """Highest-ranked unread articles."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM articles WHERE read = 0 ORDER BY rank_score DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_backlog_articles(limit: int = 20) -> list[dict]:
    """Oldest unread articles (backlog dig)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM articles WHERE read = 0 ORDER BY fetched_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def mark_articles_read(article_ids: list[int]) -> None:
    if not article_ids:
        return
    conn = get_connection()
    try:
        placeholders = ",".join("?" * len(article_ids))
        conn.execute(
            f"UPDATE articles SET read = 1 WHERE id IN ({placeholders})",
            article_ids,
        )
        conn.commit()
    finally:
        conn.close()


def count_cross_refs(url: str) -> int:
    """Count existing articles with the same URL (cross-reference detection)."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE url = ?", (url,)
        ).fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["bullet_summary"] = json.loads(d["bullet_summary"])
    return d
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_db.py -v
```

Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add newspull/db.py tests/test_db.py
git commit -m "feat: SQLite database layer with article CRUD"
```

---

## Task 4: Config Layer

**Files:**
- Create: `newspull/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config.py
import newspull.config as config_module


def test_load_prefs_creates_default_when_missing(tmp_prefs_path):
    prefs = config_module.load_prefs()
    assert "topics" in prefs
    assert "sources" in prefs
    assert "credibility" in prefs
    assert "digester" in prefs
    assert tmp_prefs_path.exists()


def test_save_and_reload_prefs(tmp_prefs_path):
    prefs = config_module.load_prefs()
    prefs["topics"]["ai"] = 0.5
    config_module.save_prefs(prefs)
    reloaded = config_module.load_prefs()
    assert reloaded["topics"]["ai"] == 0.5


def test_save_creates_backup(tmp_prefs_path):
    config_module.load_prefs()  # creates file
    config_module.save_prefs(config_module.load_prefs())
    bak = tmp_prefs_path.with_suffix(".toml.bak")
    assert bak.exists()


def test_restore_backup(tmp_prefs_path):
    prefs = config_module.load_prefs()
    original_ai_weight = prefs["topics"]["ai"]
    config_module.save_prefs(prefs)  # creates backup of original

    # Corrupt the current prefs
    prefs["topics"]["ai"] = 0.0
    config_module.save_prefs(prefs)

    config_module.restore_prefs_backup()
    restored = config_module.load_prefs()
    assert restored["topics"]["ai"] == original_ai_weight


def test_default_prefs_structure(tmp_prefs_path):
    prefs = config_module.load_prefs()
    assert isinstance(prefs["topics"], dict)
    assert isinstance(prefs["sources"]["reddit"], list)
    assert isinstance(prefs["credibility"]["min_score"], float)
    assert isinstance(prefs["digester"]["keypoints"], int)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Write `newspull/config.py`**

```python
import shutil
import tomllib
import tomli_w
from pathlib import Path

PREFS_PATH = Path.home() / ".newspull" / "preferences.toml"

DEFAULT_PREFS: dict = {
    "topics": {"ai": 1.0, "tech": 0.8, "politics": 0.3},
    "sources": {
        "reddit": ["r/MachineLearning", "r/technology"],
        "youtube": [],
        "rss": [],
        "hn": True,
    },
    "credibility": {"min_score": 0.5, "cross_ref_bonus": 0.2},
    "digester": {"style": "concise", "keypoints": 5},
}


def load_prefs() -> dict:
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not PREFS_PATH.exists():
        save_prefs(DEFAULT_PREFS)
        return _deep_copy(DEFAULT_PREFS)
    with open(PREFS_PATH, "rb") as f:
        return tomllib.load(f)


def save_prefs(prefs: dict) -> None:
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    bak_path = PREFS_PATH.with_suffix(".toml.bak")
    if PREFS_PATH.exists():
        shutil.copy2(PREFS_PATH, bak_path)
    with open(PREFS_PATH, "wb") as f:
        tomli_w.dump(prefs, f)


def restore_prefs_backup() -> bool:
    bak_path = PREFS_PATH.with_suffix(".toml.bak")
    if bak_path.exists():
        shutil.copy2(bak_path, PREFS_PATH)
        return True
    return False


def _deep_copy(d: dict) -> dict:
    import copy
    return copy.deepcopy(d)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add newspull/config.py tests/test_config.py
git commit -m "feat: preferences config layer with backup/restore"
```

---

## Task 5: Sources (RSS and HackerNews)

**Files:**
- Create: `newspull/sources/base.py`
- Create: `newspull/sources/rss.py`
- Create: `newspull/sources/hn.py`
- Create: `tests/test_sources.py` (partial — RSS + HN)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_sources.py
from unittest.mock import patch, MagicMock
import feedparser
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_sources.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write `newspull/sources/base.py`**

```python
from abc import ABC, abstractmethod
from ..models import RawArticle


class Source(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def fetch(self) -> list[RawArticle]: ...
```

- [ ] **Step 4: Write `newspull/sources/rss.py`**

```python
import httpx
import feedparser

from .base import Source
from ..models import RawArticle


class RSSSource(Source):
    def __init__(self, url: str):
        self._url = url

    @property
    def name(self) -> str:
        return f"rss:{self._url}"

    def fetch(self) -> list[RawArticle]:
        try:
            response = httpx.get(self._url, timeout=10, follow_redirects=True)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            articles = []
            for entry in feed.entries:
                url = entry.get("link", "")
                if not url:
                    continue
                content = entry.get("summary", "") or entry.get("description", "")
                articles.append(
                    RawArticle(
                        title=entry.get("title", "Untitled"),
                        url=url,
                        source="rss",
                        content=content[:4000],
                    )
                )
            return articles
        except Exception:
            return []
```

- [ ] **Step 5: Write `newspull/sources/hn.py`**

```python
import httpx

from .base import Source
from ..models import RawArticle

HN_API = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30"


class HackerNewsSource(Source):
    @property
    def name(self) -> str:
        return "hackernews"

    def fetch(self) -> list[RawArticle]:
        try:
            response = httpx.get(HN_API, timeout=10)
            response.raise_for_status()
            data = response.json()
            articles = []
            for hit in data.get("hits", []):
                url = hit.get("url", "")
                if not url:
                    continue
                content = hit.get("story_text") or f"Points: {hit.get('points', 0)}, Comments: {hit.get('num_comments', 0)}"
                articles.append(
                    RawArticle(
                        title=hit.get("title", "Untitled"),
                        url=url,
                        source="hackernews",
                        content=content[:4000],
                    )
                )
            return articles
        except Exception:
            return []
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_sources.py -v
```

Expected: 5 passed

- [ ] **Step 7: Commit**

```bash
git add newspull/sources/ tests/test_sources.py
git commit -m "feat: Source base class, RSSSource, HackerNewsSource"
```

---

## Task 6: Sources (Reddit and YouTube)

**Files:**
- Create: `newspull/sources/reddit.py`
- Create: `newspull/sources/youtube.py`
- Modify: `tests/test_sources.py` (add Reddit + YouTube tests)

- [ ] **Step 1: Add failing tests to `tests/test_sources.py`**

Append to the existing file:

```python
from newspull.sources.reddit import RedditSource
from newspull.sources.youtube import YouTubeSource

FAKE_REDDIT_RESPONSE = {
    "data": {
        "children": [
            {
                "data": {
                    "title": "Reddit Article One",
                    "url": "https://reddit.com/r/MachineLearning/comments/abc",
                    "selftext": "Some Reddit post text.",
                    "score": 500,
                }
            },
            {
                "data": {
                    "title": "Reddit Article Two",
                    "url": "https://external.com/paper",
                    "selftext": "",
                    "score": 200,
                }
            },
        ]
    }
}

FAKE_YOUTUBE_XML = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>YouTube Video One</title>
    <link href="https://www.youtube.com/watch?v=abc123"/>
    <media:group xmlns:media="http://search.yahoo.com/mrss/">
      <media:description>Video description here.</media:description>
    </media:group>
  </entry>
</feed>"""


def test_reddit_source_returns_raw_articles():
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = FAKE_REDDIT_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        source = RedditSource("r/MachineLearning")
        articles = source.fetch()

    assert len(articles) == 2
    assert articles[0].title == "Reddit Article One"
    assert articles[0].source == "reddit"


def test_reddit_source_returns_empty_on_error():
    with patch("httpx.get") as mock_get:
        mock_get.side_effect = Exception("blocked")
        source = RedditSource("r/MachineLearning")
        articles = source.fetch()
    assert articles == []


def test_youtube_source_returns_raw_articles():
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = FAKE_YOUTUBE_XML
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        source = YouTubeSource("UCtest123")
        articles = source.fetch()

    assert len(articles) == 1
    assert articles[0].title == "YouTube Video One"
    assert articles[0].source == "youtube"
    assert "youtube.com/watch" in articles[0].url


def test_youtube_source_returns_empty_on_error():
    with patch("httpx.get") as mock_get:
        mock_get.side_effect = Exception("timeout")
        source = YouTubeSource("UCtest123")
        articles = source.fetch()
    assert articles == []
```

- [ ] **Step 2: Run new tests to verify they fail**

```bash
pytest tests/test_sources.py::test_reddit_source_returns_raw_articles -v
```

Expected: `ImportError`

- [ ] **Step 3: Write `newspull/sources/reddit.py`**

```python
import httpx

from .base import Source
from ..models import RawArticle


class RedditSource(Source):
    def __init__(self, subreddit: str):
        # normalise: strip leading "r/" if present
        self._sub = subreddit.lstrip("r/")

    @property
    def name(self) -> str:
        return f"reddit:r/{self._sub}"

    def fetch(self) -> list[RawArticle]:
        url = f"https://www.reddit.com/r/{self._sub}/top.json?limit=25&t=day"
        headers = {"User-Agent": "newspull/0.1"}
        try:
            response = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
            response.raise_for_status()
            data = response.json()
            articles = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                post_url = post.get("url", "")
                if not post_url:
                    continue
                content = post.get("selftext", "") or f"Score: {post.get('score', 0)}"
                articles.append(
                    RawArticle(
                        title=post.get("title", "Untitled"),
                        url=post_url,
                        source="reddit",
                        content=content[:4000],
                    )
                )
            return articles
        except Exception:
            return []
```

- [ ] **Step 4: Write `newspull/sources/youtube.py`**

```python
import httpx
import xml.etree.ElementTree as ET

from .base import Source
from ..models import RawArticle

YT_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
}


class YouTubeSource(Source):
    def __init__(self, channel_id: str):
        self._channel_id = channel_id

    @property
    def name(self) -> str:
        return f"youtube:{self._channel_id}"

    def fetch(self) -> list[RawArticle]:
        url = YT_RSS.format(channel_id=self._channel_id)
        try:
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.text)
            articles = []
            for entry in root.findall("atom:entry", NS):
                title_el = entry.find("atom:title", NS)
                link_el = entry.find("atom:link", NS)
                desc_el = entry.find("media:group/media:description", NS)

                title = title_el.text if title_el is not None else "Untitled"
                video_url = link_el.get("href", "") if link_el is not None else ""
                content = desc_el.text if desc_el is not None else ""

                if not video_url:
                    continue
                articles.append(
                    RawArticle(
                        title=title,
                        url=video_url,
                        source="youtube",
                        content=(content or "")[:4000],
                    )
                )
            return articles
        except Exception:
            return []
```

- [ ] **Step 5: Run all source tests**

```bash
pytest tests/test_sources.py -v
```

Expected: 9 passed

- [ ] **Step 6: Commit**

```bash
git add newspull/sources/reddit.py newspull/sources/youtube.py tests/test_sources.py
git commit -m "feat: RedditSource and YouTubeSource"
```

---

## Task 7: Gatherer Agent

**Files:**
- Create: `newspull/agents/gatherer.py`
- Create: `tests/test_gatherer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_gatherer.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_gatherer.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write `newspull/agents/gatherer.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_gatherer.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add newspull/agents/gatherer.py tests/test_gatherer.py
git commit -m "feat: GathererAgent — parallel source dispatch"
```

---

## Task 8: Digester Agent

**Files:**
- Create: `newspull/agents/digester.py`
- Create: `tests/test_digester.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_digester.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_digester.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write `newspull/agents/digester.py`**

```python
import asyncio
import json
import os

from zhipuai import ZhipuAI

from ..models import RawArticle, SummarizedArticle


class DigesterAgent:
    def __init__(self):
        self.client = ZhipuAI(api_key=os.environ.get("ZHIPUAI_API_KEY", ""))

    async def digest(
        self, article: RawArticle, style: str = "concise", keypoints: int = 5
    ) -> SummarizedArticle | None:
        prompt = (
            f"Summarise this article into exactly {keypoints} bullet points.\n"
            f"Style: {style}. Be direct and informative.\n"
            f'Return JSON only: {{"title": "...", "bullets": ["...", ...]}}\n\n'
            f"Title: {article.title}\n"
            f"Content: {article.content[:3000]}"
        )
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="glm-4-flash",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            return SummarizedArticle(
                title=data.get("title", article.title),
                url=article.url,
                source=article.source,
                bullets=data["bullets"][:keypoints],
            )
        except Exception:
            return None

    async def digest_all(
        self, articles: list[RawArticle], prefs: dict
    ) -> list[SummarizedArticle]:
        style = prefs.get("digester", {}).get("style", "concise")
        keypoints = prefs.get("digester", {}).get("keypoints", 5)
        tasks = [self.digest(a, style, keypoints) for a in articles]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_digester.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add newspull/agents/digester.py tests/test_digester.py
git commit -m "feat: DigesterAgent — GLM-4-Flash batch summarisation"
```

---

## Task 9: Taster Agent

**Files:**
- Create: `newspull/agents/taster.py`
- Create: `tests/test_taster.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_taster.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_taster.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write `newspull/agents/taster.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_taster.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add newspull/agents/taster.py tests/test_taster.py
git commit -m "feat: TasterAgent — credibility scoring and preference ranking"
```

---

## Task 10: Orchestrator Agent

**Files:**
- Create: `newspull/agents/orchestrator.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_orchestrator.py
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from newspull.models import RawArticle, SummarizedArticle, RankedArticle
from newspull.agents.orchestrator import OrchestratorAgent
from datetime import datetime


def make_raw(url="https://x.com/1"):
    return RawArticle(title="T", url=url, source="hn", content="body")


def make_summary(url="https://x.com/1"):
    return SummarizedArticle(title="T", url=url, source="hn", bullets=["p1"])


def make_ranked(url="https://x.com/1"):
    return RankedArticle(
        title="T", url=url, source="hn", bullets=["p1"],
        credibility_score=0.9, rank_score=0.85, cross_ref_count=0,
        fetched_at=datetime.utcnow(),
    )


def test_orchestrator_run_saves_articles(tmp_db_path, tmp_prefs_path, default_prefs):
    import newspull.db as db
    import newspull.config as config_module
    db.init_db()
    config_module.save_prefs(default_prefs)

    with patch("newspull.agents.orchestrator.GathererAgent") as MockGatherer, \
         patch("newspull.agents.orchestrator.DigesterAgent") as MockDigester, \
         patch("newspull.agents.orchestrator.TasterAgent") as MockTaster:

        gatherer_instance = MockGatherer.return_value
        gatherer_instance.fetch_all = AsyncMock(return_value=([make_raw()], []))

        digester_instance = MockDigester.return_value
        digester_instance.digest_all = AsyncMock(return_value=[make_summary()])

        taster_instance = MockTaster.return_value
        taster_instance.taste_all = AsyncMock(return_value=[make_ranked()])

        agent = OrchestratorAgent()
        saved, errors = asyncio.run(agent.run())

    assert saved == 1
    assert errors == []
    assert len(db.get_unread_articles()) == 1


def test_orchestrator_reports_source_errors(tmp_db_path, tmp_prefs_path, default_prefs):
    import newspull.db as db
    import newspull.config as config_module
    db.init_db()
    config_module.save_prefs(default_prefs)

    with patch("newspull.agents.orchestrator.GathererAgent") as MockGatherer, \
         patch("newspull.agents.orchestrator.DigesterAgent") as MockDigester, \
         patch("newspull.agents.orchestrator.TasterAgent") as MockTaster:

        gatherer_instance = MockGatherer.return_value
        gatherer_instance.fetch_all = AsyncMock(
            return_value=([make_raw()], ["hackernews: timeout"])
        )
        digester_instance = MockDigester.return_value
        digester_instance.digest_all = AsyncMock(return_value=[make_summary()])
        taster_instance = MockTaster.return_value
        taster_instance.taste_all = AsyncMock(return_value=[make_ranked()])

        agent = OrchestratorAgent()
        saved, errors = asyncio.run(agent.run())

    assert saved == 1
    assert len(errors) == 1


def test_orchestrator_returns_zero_when_no_articles(tmp_db_path, tmp_prefs_path, default_prefs):
    import newspull.db as db
    import newspull.config as config_module
    db.init_db()
    config_module.save_prefs(default_prefs)

    with patch("newspull.agents.orchestrator.GathererAgent") as MockGatherer, \
         patch("newspull.agents.orchestrator.DigesterAgent") as MockDigester, \
         patch("newspull.agents.orchestrator.TasterAgent") as MockTaster:

        gatherer_instance = MockGatherer.return_value
        gatherer_instance.fetch_all = AsyncMock(return_value=([], ["all sources failed"]))

        agent = OrchestratorAgent()
        saved, errors = asyncio.run(agent.run())

    assert saved == 0
    assert len(errors) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write `newspull/agents/orchestrator.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add newspull/agents/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: OrchestratorAgent — async pipeline coordinator"
```

---

## Task 11: Feedback Agent

**Files:**
- Create: `newspull/agents/feedback.py`
- Create: `tests/test_feedback.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_feedback.py
import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest

from newspull.agents.feedback import FeedbackAgent, deep_merge
import newspull.config as config_module


def make_llm_response(delta: dict) -> MagicMock:
    msg = MagicMock()
    msg.content = json.dumps(delta)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_deep_merge_updates_nested():
    base = {"topics": {"ai": 1.0, "tech": 0.8}, "digester": {"keypoints": 5}}
    delta = {"digester": {"keypoints": 7, "style": "simple"}}
    result = deep_merge(base, delta)
    assert result["digester"]["keypoints"] == 7
    assert result["digester"]["style"] == "simple"
    assert result["topics"]["ai"] == 1.0  # unchanged


def test_deep_merge_does_not_mutate_base():
    base = {"a": {"b": 1}}
    delta = {"a": {"b": 2}}
    deep_merge(base, delta)
    assert base["a"]["b"] == 1


def test_feedback_agent_updates_prefs(tmp_prefs_path, default_prefs):
    config_module.save_prefs(default_prefs)

    with patch("newspull.agents.feedback.ZhipuAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create.return_value = make_llm_response(
            {"digester": {"style": "simple", "keypoints": 7}}
        )
        agent = FeedbackAgent()
        success = asyncio.run(agent.process("please use simpler language and add more keypoints"))

    assert success is True
    prefs = config_module.load_prefs()
    assert prefs["digester"]["style"] == "simple"
    assert prefs["digester"]["keypoints"] == 7
    assert prefs["topics"]["ai"] == 1.0  # unchanged


def test_feedback_agent_returns_false_on_llm_error(tmp_prefs_path, default_prefs):
    config_module.save_prefs(default_prefs)

    with patch("newspull.agents.feedback.ZhipuAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create.side_effect = Exception("API error")
        agent = FeedbackAgent()
        success = asyncio.run(agent.process("make it simpler"))

    assert success is False
    # Prefs should be unchanged
    prefs = config_module.load_prefs()
    assert prefs["digester"]["keypoints"] == default_prefs["digester"]["keypoints"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_feedback.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write `newspull/agents/feedback.py`**

```python
import asyncio
import json
import os

from zhipuai import ZhipuAI

from ..config import load_prefs, save_prefs


def deep_merge(base: dict, update: dict) -> dict:
    result = base.copy()
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class FeedbackAgent:
    def __init__(self):
        self.client = ZhipuAI(api_key=os.environ.get("ZHIPUAI_API_KEY", ""))

    async def process(self, review_text: str) -> bool:
        prefs = load_prefs()
        prompt = (
            f'User feedback about their news feed: "{review_text}"\n\n'
            f"Current preferences:\n{json.dumps(prefs, indent=2)}\n\n"
            "Return a JSON object with only the keys that should change. "
            "Use the same structure as the preferences. Only include modified sections.\n"
            'Example: {"digester": {"style": "simple", "keypoints": 7}}'
        )
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="glm-4-air",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            delta = json.loads(response.choices[0].message.content)
            merged = deep_merge(prefs, delta)
            save_prefs(merged)
            return True
        except Exception:
            return False
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_feedback.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add newspull/agents/feedback.py tests/test_feedback.py
git commit -m "feat: FeedbackAgent — natural language preferences update via GLM-4-Air"
```

---

## Task 12: CLI

**Files:**
- Create: `newspull/cli/main.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_cli.py
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import json

from newspull.cli.main import app

runner = CliRunner()


def make_db_article(n=1):
    return {
        "id": n,
        "title": f"Article {n}",
        "url": f"https://example.com/{n}",
        "source": "hackernews",
        "bullet_summary": ["Point one", "Point two", "Point three"],
        "credibility_score": 0.9,
        "rank_score": 0.85,
        "cross_ref_count": 1,
        "fetched_at": datetime.utcnow().isoformat(),
        "read": 0,
    }


def test_default_command_shows_feed(tmp_db_path):
    import newspull.db as db
    db.init_db()

    with patch("newspull.cli.main.db.get_unread_articles", return_value=[make_db_article()]), \
         patch("newspull.cli.main.db.mark_articles_read"), \
         patch("newspull.cli.main.typer.prompt", return_value="n"):
        result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Article 1" in result.output


def test_default_command_shows_empty_message(tmp_db_path):
    import newspull.db as db
    db.init_db()

    with patch("newspull.cli.main.db.get_unread_articles", return_value=[]):
        result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "newspull fetch" in result.output


def test_fetch_command_runs_pipeline(tmp_db_path, tmp_prefs_path, default_prefs):
    import newspull.config as config_module
    config_module.save_prefs(default_prefs)

    with patch("newspull.cli.main.asyncio.run", return_value=(3, [])):
        result = runner.invoke(app, ["fetch"])

    assert result.exit_code == 0
    assert "3" in result.output


def test_fetch_command_reports_errors(tmp_db_path, tmp_prefs_path, default_prefs):
    import newspull.config as config_module
    config_module.save_prefs(default_prefs)

    with patch("newspull.cli.main.asyncio.run", return_value=(1, ["reddit: timeout"])):
        result = runner.invoke(app, ["fetch"])

    assert result.exit_code == 0
    assert "reddit" in result.output


def test_pull_command_shows_backlog(tmp_db_path):
    import newspull.db as db
    db.init_db()

    with patch("newspull.cli.main.db.get_backlog_articles", return_value=[make_db_article()]), \
         patch("newspull.cli.main.db.mark_articles_read"), \
         patch("newspull.cli.main.typer.prompt", return_value="n"):
        result = runner.invoke(app, ["pull"])

    assert result.exit_code == 0
    assert "Article 1" in result.output


def test_config_add_source(tmp_prefs_path, default_prefs):
    import newspull.config as config_module
    config_module.save_prefs(default_prefs)

    result = runner.invoke(app, ["config", "add-source", "reddit", "r/Python"])
    assert result.exit_code == 0
    prefs = config_module.load_prefs()
    assert "r/Python" in prefs["sources"]["reddit"]


def test_config_remove_source(tmp_prefs_path, default_prefs):
    import newspull.config as config_module
    config_module.save_prefs(default_prefs)

    result = runner.invoke(app, ["config", "remove-source", "reddit", "r/MachineLearning"])
    assert result.exit_code == 0
    prefs = config_module.load_prefs()
    assert "r/MachineLearning" not in prefs["sources"]["reddit"]


def test_config_set_weight(tmp_prefs_path, default_prefs):
    import newspull.config as config_module
    config_module.save_prefs(default_prefs)

    result = runner.invoke(app, ["config", "set-weight", "topic", "ai", "0.5"])
    assert result.exit_code == 0
    prefs = config_module.load_prefs()
    assert prefs["topics"]["ai"] == 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cli.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write `newspull/cli/main.py`**

```python
import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.rule import Rule

from newspull import db
from newspull.config import load_prefs, save_prefs
from newspull.agents.orchestrator import OrchestratorAgent
from newspull.agents.feedback import FeedbackAgent

app = typer.Typer(invoke_without_command=True)
config_app = typer.Typer()
app.add_typer(config_app, name="config")
console = Console()


@app.callback(invoke_without_command=True)
def show_feed(ctx: typer.Context):
    """Show your ranked news feed. All shown stories are marked read."""
    if ctx.invoked_subcommand is not None:
        return
    db.init_db()
    articles = db.get_unread_articles(limit=20)
    if not articles:
        console.print(
            "No new stories. Run [bold]newspull fetch[/bold] to pull fresh content,"
            " or [bold]newspull pull[/bold] to dig into your backlog."
        )
        return
    _render_feed(articles)
    db.mark_articles_read([a["id"] for a in articles])
    _review_prompt()


@app.command()
def pull():
    """Dig into backlog — fetched but not yet displayed articles."""
    db.init_db()
    articles = db.get_backlog_articles(limit=20)
    if not articles:
        console.print(
            "No backlog. Run [bold]newspull fetch[/bold] to pull fresh content."
        )
        return
    _render_feed(articles)
    db.mark_articles_read([a["id"] for a in articles])
    _review_prompt()


@app.command()
def fetch():
    """Trigger full agent pipeline — fetch new content from all sources."""
    console.print("Fetching...")
    agent = OrchestratorAgent()
    saved, errors = asyncio.run(agent.run())
    console.print(f"[green]✓[/green] Saved {saved} new articles.")
    for err in errors:
        console.print(f"[yellow]⚠[/yellow] {err}")


@app.command()
def feedback():
    """Invoke Feedback agent to review and change your preferences."""
    _review_prompt(force=True)


@app.command()
def web(port: int = 5001):
    """Start the web feed viewer in your browser."""
    import webbrowser
    from newspull.web.app import create_app
    flask_app = create_app()
    url = f"http://localhost:{port}"
    webbrowser.open(url)
    flask_app.run(port=port, debug=False)


@config_app.command("add-source")
def config_add_source(source_type: str, value: str):
    """Add a source. E.g.: add-source reddit r/MachineLearning"""
    prefs = load_prefs()
    sources = prefs.setdefault("sources", {})
    lst = sources.setdefault(source_type.lower(), [])
    if value not in lst:
        lst.append(value)
        save_prefs(prefs)
        console.print(f"[green]✓[/green] Added {source_type}:{value}")
    else:
        console.print(f"Already present: {source_type}:{value}")


@config_app.command("remove-source")
def config_remove_source(source_type: str, value: str):
    """Remove a source. E.g.: remove-source reddit r/MachineLearning"""
    prefs = load_prefs()
    lst = prefs.get("sources", {}).get(source_type.lower(), [])
    if value in lst:
        lst.remove(value)
        save_prefs(prefs)
        console.print(f"[green]✓[/green] Removed {source_type}:{value}")
    else:
        console.print(f"Not found: {source_type}:{value}")


@config_app.command("set-weight")
def config_set_weight(category: str, key: str, value: float):
    """Set a topic or source weight. E.g.: set-weight topic ai 0.9"""
    prefs = load_prefs()
    category_key = f"{category}s" if not category.endswith("s") else category
    if category_key not in prefs:
        prefs[category_key] = {}
    prefs[category_key][key] = value
    save_prefs(prefs)
    console.print(f"[green]✓[/green] Set {category_key}.{key} = {value}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_feed(articles: list[dict]) -> None:
    for i, article in enumerate(articles, 1):
        stars = f"★ {article['credibility_score']:.2f}"
        src_count = article.get("cross_ref_count", 0)
        src_label = f"· {src_count} src" if src_count > 1 else ""
        console.rule(
            f"[bold][#{i}] {article['title']}[/bold]  {stars}  {src_label}"
        )
        for bullet in article["bullet_summary"]:
            console.print(f"  • {bullet}")
        console.print(f"  [dim]· {article['source']} · {article['url']}[/dim]")
        console.print()


def _review_prompt(force: bool = False) -> None:
    answer = typer.prompt("Do you want to leave a review?", default="n")
    if answer.lower() not in ("y", "yes"):
        return
    review = typer.prompt("Type your review below")
    if review.strip():
        agent = FeedbackAgent()
        success = asyncio.run(agent.process(review))
        if success:
            console.print("[green]✓ Got it — preferences updated.[/green]")
        else:
            console.print("[red]Could not update preferences. Check your API key.[/red]")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cli.py -v
```

Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add newspull/cli/main.py tests/test_cli.py
git commit -m "feat: CLI — newspull, pull, fetch, feedback, web, config commands"
```

---

## Task 13: Web UI

**Files:**
- Create: `newspull/web/app.py`
- Create: `newspull/web/templates/index.html`
- Create: `tests/test_web.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_web.py
import json
from datetime import datetime
from unittest.mock import patch

import pytest

from newspull.web.app import create_app


@pytest.fixture
def client(tmp_db_path):
    import newspull.db as db
    db.init_db()
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


def make_db_article(n=1):
    return {
        "id": n,
        "title": f"Article {n}",
        "url": f"https://example.com/{n}",
        "source": "hackernews",
        "bullet_summary": ["Point one", "Point two"],
        "credibility_score": 0.9,
        "rank_score": 0.85,
        "cross_ref_count": 1,
        "fetched_at": datetime.utcnow().isoformat(),
        "read": 0,
    }


def test_index_returns_200(client, tmp_db_path):
    with patch("newspull.web.app.db.get_unread_articles", return_value=[make_db_article()]):
        response = client.get("/")
    assert response.status_code == 200
    assert b"Article 1" in response.data


def test_index_shows_empty_state(client, tmp_db_path):
    with patch("newspull.web.app.db.get_unread_articles", return_value=[]):
        response = client.get("/")
    assert response.status_code == 200
    assert b"newspull fetch" in response.data


def test_mark_read_endpoint(client, tmp_db_path):
    with patch("newspull.web.app.db.mark_articles_read") as mock_mark:
        response = client.post(
            "/mark-read",
            data=json.dumps({"ids": [1, 2]}),
            content_type="application/json",
        )
    assert response.status_code == 200
    mock_mark.assert_called_once_with([1, 2])


def test_review_endpoint_calls_feedback(client, tmp_db_path, tmp_prefs_path, default_prefs):
    import newspull.config as config_module
    config_module.save_prefs(default_prefs)

    with patch("newspull.web.app.FeedbackAgent") as MockFeedback:
        instance = MockFeedback.return_value
        from unittest.mock import AsyncMock
        instance.process = AsyncMock(return_value=True)

        response = client.post(
            "/review",
            data=json.dumps({"review": "use simpler language"}),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True


def test_fetch_endpoint_runs_pipeline(client, tmp_db_path, tmp_prefs_path, default_prefs):
    import newspull.config as config_module
    config_module.save_prefs(default_prefs)

    with patch("newspull.web.app.asyncio.run", return_value=(5, [])):
        response = client.post("/fetch")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["saved"] == 5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_web.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write `newspull/web/app.py`**

```python
import asyncio

from flask import Flask, render_template, request, jsonify

from newspull import db
from newspull.agents.feedback import FeedbackAgent
from newspull.agents.orchestrator import OrchestratorAgent


def create_app() -> Flask:
    app = Flask(__name__)
    db.init_db()

    @app.route("/")
    def index():
        articles = db.get_unread_articles(limit=30)
        return render_template("index.html", articles=articles)

    @app.route("/mark-read", methods=["POST"])
    def mark_read():
        ids = request.json.get("ids", [])
        db.mark_articles_read(ids)
        return jsonify({"ok": True})

    @app.route("/review", methods=["POST"])
    def review():
        text = request.json.get("review", "").strip()
        if not text:
            return jsonify({"success": False, "error": "empty review"}), 400
        agent = FeedbackAgent()
        success = asyncio.run(agent.process(text))
        return jsonify({"success": success})

    @app.route("/fetch", methods=["POST"])
    def fetch():
        agent = OrchestratorAgent()
        saved, errors = asyncio.run(agent.run())
        return jsonify({"saved": saved, "errors": errors})

    return app
```

- [ ] **Step 4: Write `newspull/web/templates/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NewsPull</title>
  <script src="https://unpkg.com/htmx.org@1.9.12"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #0f0f0f; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 1rem; }
    header { display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; border-bottom: 1px solid #333; margin-bottom: 1.5rem; }
    header h1 { font-size: 1.4rem; color: #fff; }
    .btn { background: #222; border: 1px solid #444; color: #e0e0e0; padding: 0.4rem 0.9rem; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }
    .btn:hover { background: #333; }
    .article { border: 1px solid #222; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; }
    .article-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem; }
    .article-title { font-weight: 600; font-size: 1rem; color: #fff; flex: 1; margin-right: 1rem; }
    .article-meta { font-size: 0.8rem; color: #888; white-space: nowrap; }
    .score { color: #f0c040; }
    ul.bullets { list-style: disc; padding-left: 1.4rem; }
    ul.bullets li { margin: 0.3rem 0; font-size: 0.92rem; color: #ccc; }
    .source-tag { font-size: 0.78rem; color: #666; margin-top: 0.5rem; }
    .empty { text-align: center; padding: 3rem; color: #666; }
    .empty code { background: #1a1a1a; padding: 0.2rem 0.5rem; border-radius: 3px; color: #aaa; }
    .review-section { margin-top: 2rem; border-top: 1px solid #333; padding-top: 1.5rem; }
    .review-section h3 { font-size: 0.95rem; color: #aaa; margin-bottom: 0.8rem; }
    .review-form { display: flex; gap: 0.6rem; }
    .review-input { flex: 1; background: #1a1a1a; border: 1px solid #333; color: #e0e0e0; padding: 0.5rem 0.8rem; border-radius: 4px; font-size: 0.9rem; }
    .review-input:focus { outline: none; border-color: #555; }
    #review-result { margin-top: 0.6rem; font-size: 0.85rem; color: #4caf50; }
  </style>
</head>
<body>
  <header>
    <h1>NewsPull</h1>
    <div>
      <button class="btn" hx-post="/fetch" hx-swap="none"
              hx-on::after-request="document.location.reload()">Fetch</button>
    </div>
  </header>

  {% if articles %}
    {% for article in articles %}
    <div class="article" id="article-{{ article.id }}">
      <div class="article-header">
        <a class="article-title" href="{{ article.url }}" target="_blank" rel="noopener">
          {{ article.title }}
        </a>
        <span class="article-meta">
          <span class="score">★ {{ "%.2f"|format(article.credibility_score) }}</span>
          {% if article.cross_ref_count > 1 %}
            &nbsp;· {{ article.cross_ref_count }} src
          {% endif %}
        </span>
      </div>
      <ul class="bullets">
        {% for bullet in article.bullet_summary %}
        <li>{{ bullet }}</li>
        {% endfor %}
      </ul>
      <div class="source-tag">· {{ article.source }}</div>
    </div>
    {% endfor %}

    <script>
      // Mark all displayed articles as read
      const ids = [{% for a in articles %}{{ a.id }}{% if not loop.last %},{% endif %}{% endfor %}];
      fetch('/mark-read', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ids})
      });
    </script>
  {% else %}
    <div class="empty">
      <p>No new stories.</p>
      <p style="margin-top:0.5rem">Run <code>newspull fetch</code> to pull fresh content.</p>
    </div>
  {% endif %}

  <div class="review-section">
    <h3>Leave a review to tune your feed</h3>
    <div class="review-form">
      <input class="review-input" id="review-input" type="text"
             placeholder="e.g. use simpler language, add more keypoints…">
      <button class="btn"
              hx-post="/review"
              hx-vals='js:{"review": document.getElementById("review-input").value}'
              hx-target="#review-result"
              hx-swap="innerHTML">Send</button>
    </div>
    <div id="review-result"></div>
  </div>

  <script>
    document.body.addEventListener('htmx:afterRequest', function(evt) {
      if (evt.detail.pathInfo && evt.detail.pathInfo.requestPath === '/review') {
        try {
          const resp = JSON.parse(evt.detail.xhr.responseText);
          document.getElementById('review-result').textContent =
            resp.success ? '✓ Preferences updated.' : '✗ Could not update. Check API key.';
          if (resp.success) document.getElementById('review-input').value = '';
        } catch(e) {}
      }
    });
  </script>
</body>
</html>
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_web.py -v
```

Expected: 5 passed

- [ ] **Step 6: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests pass. Note any failures and fix before committing.

- [ ] **Step 7: Commit**

```bash
git add newspull/web/ tests/test_web.py
git commit -m "feat: Flask web UI with HTMX feed, mark-read, review, fetch endpoints"
```

---

## Verification Checklist

After all tasks are complete, verify end-to-end:

- [ ] **1. Set API key**
  ```bash
  export ZHIPUAI_API_KEY="your-key-here"
  ```

- [ ] **2. Run full test suite**
  ```bash
  pytest tests/ -v
  ```
  Expected: All tests pass.

- [ ] **3. CLI fetch**
  ```bash
  newspull fetch
  ```
  Expected: "Saved N new articles." (or errors reported per source).

- [ ] **4. CLI feed**
  ```bash
  newspull
  ```
  Expected: Articles render with bullets, credibility score, source. Review prompt appears.

- [ ] **5. CLI backlog**
  ```bash
  newspull pull
  ```
  Expected: Older unread articles shown.

- [ ] **6. Web view**
  ```bash
  newspull web
  ```
  Expected: Browser opens at `http://localhost:5001`. Feed visible, review box works.

- [ ] **7. Config commands**
  ```bash
  newspull config add-source reddit r/Python
  newspull config set-weight topic python 0.9
  newspull config remove-source reddit r/Python
  ```
  Expected: `~/.newspull/preferences.toml` updated after each command.

- [ ] **8. Review / feedback**
  Leave a review: "use simpler language and add more bullet points"
  Expected: `~/.newspull/preferences.toml` → `digester.style` and `keypoints` updated.
