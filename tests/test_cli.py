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
