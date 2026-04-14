from datetime import datetime, timezone

import pytest


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
    from newspull.models import RawArticle
    return RawArticle(
        title="GLM-5 Announced With Major Improvements",
        url="https://example.com/glm5",
        source="hackernews",
        content="Zhipu AI has announced GLM-5 with significant improvements in reasoning and code generation. The model outperforms previous versions on standard benchmarks.",
    )


@pytest.fixture
def sample_ranked_article():
    from newspull.models import RankedArticle
    return RankedArticle(
        title="GLM-5 Announced With Major Improvements",
        url="https://example.com/glm5",
        source="hackernews",
        bullets=["Zhipu AI released GLM-5", "Improved reasoning and code gen", "Beats benchmarks"],
        credibility_score=0.9,
        rank_score=0.85,
        cross_ref_count=0,
        fetched_at=datetime.now(timezone.utc),
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
