# tests/test_web.py
import json
from datetime import datetime, timezone
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
        "fetched_at": datetime.now(timezone.utc).isoformat(),
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

    from unittest.mock import AsyncMock

    with patch("newspull.web.app.OrchestratorAgent") as MockOrchestrator:
        instance = MockOrchestrator.return_value
        instance.run = AsyncMock(return_value=(5, []))

        response = client.post("/fetch")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["saved"] == 5
