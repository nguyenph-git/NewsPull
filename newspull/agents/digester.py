import asyncio
import json
import os
import logging

from zhipuai import ZhipuAI

from ..models import RawArticle, SummarizedArticle

logger = logging.getLogger(__name__)


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
                model="glm-4",
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
        except Exception as e:
            error_msg = str(e)
            logger.error("Failed to summarize article %s: %s", article.url, e)

            # Parse zhipuai error for better user feedback
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    error_data = e.response.json()
                    if error_data.get('error', {}).get('code') == 1211:
                        logger.error("Model does not exist - check model name in digester.py")
                        raise ValueError(
                            "GLM model not found. Please verify:\n"
                            "  1. Your API key has access to the model\n"
                            "  2. Current model in digester.py: glm-4\n"
                            "  3. Try alternate models in z.ai console"
                        )
                except:
                    pass
            return None

    async def digest_all(
        self, articles: list[RawArticle], prefs: dict
    ) -> list[SummarizedArticle]:
        style = prefs.get("digester", {}).get("style", "concise")
        keypoints = prefs.get("digester", {}).get("keypoints", 5)
        tasks = [self.digest(a, style, keypoints) for a in articles]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
