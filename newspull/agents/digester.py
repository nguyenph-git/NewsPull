import asyncio
import json
import os

from zhipuai import ZhipuAI

from ..models import RawArticle, SummarizedArticle


class DigesterAgent:
    def __init__(self):
        self.client = ZhipuAI(api_key=os.environ.get("ZHIPUAI_API_KEY", ""))
        self._sem = asyncio.Semaphore(8)

    async def digest(
        self, article: RawArticle, style: str = "concise", keypoints: int = 5
    ) -> SummarizedArticle | None:
        prompt = (
            f"Summarise this article into exactly {keypoints} bullet points.\n"
            f"Style: {style}. Be direct and informative.\n"
            f"You MUST respond with valid JSON and nothing else — no markdown, no code fences.\n"
            f'Format: {{"title": "...", "bullets": ["...", ...]}}\n\n'
            f"Title: {article.title}\n"
            f"Content: {article.content[:3000]}"
        )
        try:
            async with self._sem:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model="GLM-4.5",
                    messages=[{"role": "user", "content": prompt}],
                )
            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if model wraps the JSON
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw.strip())
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
