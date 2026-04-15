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
