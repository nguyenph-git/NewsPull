import asyncio

import typer
from rich.console import Console

from newspull import db
from newspull.config import load_prefs, save_prefs
from newspull.agents.orchestrator import OrchestratorAgent
from newspull.agents.feedback import FeedbackAgent

app = typer.Typer(invoke_without_command=True)
config_app = typer.Typer()
app.add_typer(config_app, name="config")
console = Console()


@app.callback(invoke_without_command=True)
def show_feed(ctx: typer.Context):
    """Show your ranked news feed. All shown stories are marked read."""
    if ctx.invoked_subcommand is not None:
        return
    db.init_db()
    articles = db.get_unread_articles(limit=20)
    if not articles:
        console.print(
            "No new stories. Run [bold]newspull fetch[/bold] to pull fresh content,"
            " or [bold]newspull pull[/bold] to dig into your backlog."
        )
        return
    _render_feed(articles)
    db.mark_articles_read([a["id"] for a in articles])
    _review_prompt()


@app.command()
def pull():
    """Dig into backlog — fetched but not yet displayed articles."""
    db.init_db()
    articles = db.get_backlog_articles(limit=20)
    if not articles:
        console.print(
            "No backlog. Run [bold]newspull fetch[/bold] to pull fresh content."
        )
        return
    _render_feed(articles)
    db.mark_articles_read([a["id"] for a in articles])
    _review_prompt()


@app.command()
def fetch():
    """Trigger full agent pipeline — fetch new content from all sources."""
    db.init_db()
    console.print("Fetching...")
    agent = OrchestratorAgent()
    saved, errors = asyncio.run(agent.run())
    console.print(f"[green]✓[/green] Saved {saved} new articles.")
    for err in errors:
        console.print(f"[yellow]⚠[/yellow] {err}")


@app.command()
def feedback():
    """Invoke Feedback agent to review and change your preferences."""
    _review_prompt(force=True)


@app.command()
def web(port: int = 5001):
    """Start the web feed viewer in your browser."""
    import webbrowser
    from newspull.web.app import create_app
    flask_app = create_app()
    url = f"http://localhost:{port}"
    webbrowser.open(url)
    flask_app.run(port=port, debug=False)


@config_app.command("add-source")
def config_add_source(source_type: str, value: str):
    """Add a source. E.g.: add-source reddit r/MachineLearning"""
    prefs = load_prefs()
    sources = prefs.setdefault("sources", {})
    lst = sources.setdefault(source_type.lower(), [])
    if value not in lst:
        lst.append(value)
        save_prefs(prefs)
        console.print(f"[green]✓[/green] Added {source_type}:{value}")
    else:
        console.print(f"Already present: {source_type}:{value}")


@config_app.command("remove-source")
def config_remove_source(source_type: str, value: str):
    """Remove a source. E.g.: remove-source reddit r/MachineLearning"""
    prefs = load_prefs()
    lst = prefs.get("sources", {}).get(source_type.lower(), [])
    if value in lst:
        lst.remove(value)
        save_prefs(prefs)
        console.print(f"[green]✓[/green] Removed {source_type}:{value}")
    else:
        console.print(f"Not found: {source_type}:{value}")


@config_app.command("set-weight")
def config_set_weight(category: str, key: str, value: float):
    """Set a topic or source weight. E.g.: set-weight topic ai 0.9"""
    _CATEGORY_MAP = {
        "topic": "topics",
        "topics": "topics",
        "source": "sources",
        "sources": "sources",
        "credibility": "credibility",
        "digester": "digester",
    }
    prefs = load_prefs()
    category_key = _CATEGORY_MAP.get(category.lower(), category)
    if category_key not in prefs:
        prefs[category_key] = {}
    prefs[category_key][key] = value
    save_prefs(prefs)
    console.print(f"[green]✓[/green] Set {category_key}.{key} = {value}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_feed(articles: list[dict]) -> None:
    for i, article in enumerate(articles, 1):
        stars = f"★ {article['credibility_score']:.2f}"
        src_count = article.get("cross_ref_count", 0)
        src_label = f"· {src_count} src" if src_count > 1 else ""
        console.rule(
            f"[bold][#{i}] {article['title']}[/bold]  {stars}  {src_label}"
        )
        for bullet in article["bullet_summary"]:
            console.print(f"  • {bullet}")
        console.print(f"  [dim]· {article['source']} · {article['url']}[/dim]")
        console.print()


def _review_prompt(force: bool = False) -> None:
    if not force:
        answer = typer.prompt("Do you want to leave a review?", default="n")
        if answer.lower() not in ("y", "yes"):
            return
    review = typer.prompt("Type your review below")
    if review.strip():
        agent = FeedbackAgent()
        success = asyncio.run(agent.process(review))
        if success:
            console.print("[green]✓ Got it — preferences updated.[/green]")
        else:
            console.print("[red]Could not update preferences. Check your API key.[/red]")
