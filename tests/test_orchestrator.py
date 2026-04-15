import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from newspull.models import RawArticle, SummarizedArticle, RankedArticle
from newspull.agents.orchestrator import OrchestratorAgent
from datetime import datetime, UTC


def make_raw(url="https://x.com/1"):
    return RawArticle(title="T", url=url, source="hn", content="body")


def make_summary(url="https://x.com/1"):
    return SummarizedArticle(title="T", url=url, source="hn", bullets=["p1"])


def make_ranked(url="https://x.com/1"):
    return RankedArticle(
        title="T", url=url, source="hn", bullets=["p1"],
        credibility_score=0.9, rank_score=0.85, cross_ref_count=0,
        fetched_at=datetime.now(UTC),
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
