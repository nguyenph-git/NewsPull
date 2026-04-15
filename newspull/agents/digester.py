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
