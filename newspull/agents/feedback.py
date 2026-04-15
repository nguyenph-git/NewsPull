import asyncio
import copy
import json
import logging
import os

from zhipuai import ZhipuAI

from ..config import load_prefs, save_prefs

logger = logging.getLogger(__name__)


def deep_merge(base: dict, update: dict) -> dict:
    result = copy.deepcopy(base)
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
        except Exception as exc:
            logger.debug("FeedbackAgent.process failed: %s", exc)
            return False
