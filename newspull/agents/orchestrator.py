import asyncio

from rich.console import Console
from rich import print as rprint

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

console = Console()


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
        import os

        # Check API key early
        if not os.environ.get("ZHIPUAI_API_KEY"):
            print("[red]✗[/red] ZHIPUAI_API_KEY not set!")
            print("[yellow]Set it in your .env file:[/yellow]")
            print("  ZHIPUAI_API_KEY=your-api-key-here")
            return 0, ["API key not configured"]

        prefs = load_prefs()
        sources = self._build_sources(prefs)

        if not sources:
            print("[yellow]⚠[/yellow] No sources configured. Add sources with:")
            print("  newspull config add-source reddit r/MachineLearning")
            print("  newspull config add-source rss https://example.com/feed.xml")
            return 0, ["No sources configured"]

        gatherer = GathererAgent(sources)
        digester = DigesterAgent()
        taster = TasterAgent()

        print(f"[cyan]→[/cyan] Fetching from {len(sources)} source(s)...")
        raw_articles, errors = await gatherer.fetch_all()
        if not raw_articles:
            print(f"[yellow]⚠[/yellow] No articles fetched from any source.")
            if errors:
                print("[red]Errors:[/red]")
                for err in errors:
                    print(f"  [red]•[/red] {err}")
            return 0, errors

        print(f"[cyan]→[/cyan] Summarizing {len(raw_articles)} article(s)...")
        summaries = await digester.digest_all(raw_articles, prefs)
        if not summaries:
            print(f"[red]✗[/red] Summarization failed for all articles!")
            print("[yellow]Common causes:[/yellow]")
            print("  • API key is invalid or missing")
            print("  • Check your .env file: cat .env")
            print("  • Verify API key: https://open.bigmodel.cn/usercenter/apikeys")
            print("  • Check logs: tail -f ~/.newspull/newspull.log 2>/dev/null")
            return 0, errors

        print(f"[cyan]→[/cyan] Scoring and ranking {len(summaries)} article(s)...")
        ranked = await taster.taste_all(summaries, prefs)

        print(f"[cyan]→[/cyan] Saving to database...")
        saved = 0
        for article in ranked:
            if db.save_article(article) is not None:
                saved += 1

        print(f"[green]✓[/green] Pipeline complete: {saved} article(s) saved, {len(errors)} error(s)")
        return saved, errors
