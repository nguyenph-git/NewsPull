# NewsPull — Design Spec

**Date:** 2026-04-15

## Context

NewsPull is a personal news aggregation and AI summarisation system. The goal is to automatically gather content from multiple sources, distil it into concise bullet-point summaries, verify credibility, and surface a ranked feed that adapts to the user's evolving preferences. The user wants fast on-demand reading via CLI, an optional web view, and a natural-language feedback loop to tune the system over time without manual config editing.

---

## Agents (AGNO, 5 agents)

| Agent | Responsibility |
|---|---|
| **Orchestrator** | Entry point. Spawns Gatherers in parallel, coordinates pipeline, receives ranked results from Taster, presents feed. |
| **Gatherer** | One instance per source. Fetches raw content using `httpx` (RSS/APIs) or Playwright (JS-heavy: Reddit, YouTube). Passes raw articles in-memory to Digester. |
| **Digester** | Receives raw article. Calls GLM-4-Flash to produce 3–5 bullet-point summary. Passes summary in-memory to Taster. Raw content is never persisted. |
| **Taster** | Receives summary. Scores credibility: source reputation weight + cross-reference bonus (queries SQLite for matching URL/title from other sources). Applies user preferences from `preferences.toml`. Returns ranked result to Orchestrator. |
| **Feedback** | On-demand only. Invoked after feed session via review prompt, or via `newspull feedback`. Accepts natural-language input, interprets it, updates `preferences.toml`. |

---

## Parallel Execution

Gatherer, Digester, and Taster all run in parallel batches (AGNO async). Multiple Gatherers run simultaneously (one per source). Digester and Taster process article batches concurrently. Raw content flows in-memory; only the final processed article hits SQLite.

**Data pipeline:**
```
Gatherer (parallel) → [raw, in-memory] → Digester (parallel) → [summary, in-memory] → Taster (parallel) → SQLite
```

---

## Storage (SQLite)

**Tables:**
- `articles` — id, source, url, timestamp, bullet_summary (JSON array), credibility_score, rank, read (bool)
- `feed_history` — session_id, article_id, shown_at

---

## Global Preferences (`~/.newspull/preferences.toml`)

```toml
[topics]
ai = 1.0
tech = 0.8
politics = 0.3

[sources]
reddit = ["r/MachineLearning", "r/technology"]
youtube = ["channel_id_1"]
rss = ["https://example.com/feed.xml"]

[credibility]
min_score = 0.5
cross_ref_bonus = 0.2

[digester]
style = "concise"   # updated by Feedback agent from natural language
keypoints = 5
```

All agents read from this file. Only the Feedback agent writes to it.

---

## CLI

```bash
newspull                   # show latest feed; all shown stories auto-marked read; review prompt after
newspull pull              # show backlog — fetched but not yet displayed articles
newspull fetch             # trigger full agent pipeline to pull new content from sources
newspull feedback          # invoke Feedback agent directly to review/change preferences
newspull web               # start local Flask web server on port 5001, open browser
newspull web --port 8080
newspull config add-source reddit r/MachineLearning
newspull config remove-source reddit r/MachineLearning
newspull config set-weight topic ai 0.9
```

**Feed display:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[#1] GPT-5 released with reasoning improvements  ★ 0.92  · 3 sources
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • OpenAI announced GPT-5 with improved chain-of-thought reasoning
  • Benchmarks show 40% improvement on MATH and coding tasks
  • Available via API immediately, ChatGPT rollout next week
  • Priced same as GPT-4o
  · r/MachineLearning · HackerNews · TheVerge
```

**Review prompt (after every feed session):**
```
Do you want to leave a review? [y/N]: y

Type your review below:
> the language used was too complex, please dumb it down and add more keypoints

✓ Got it — preferences updated.
```

---

## Web View (Flask + HTMX)

Simple local server started by `newspull web`. Reads from SQLite. Mirrors CLI feed layout. Review box at the bottom. Marks articles read on view. No external JS frameworks — HTMX only.

---

## LLM Models (Zhipu AI GLM)

| Agent | Model | Reason |
|---|---|---|
| Digester | **GLM-4-Flash** | High volume, speed + low cost matter most |
| Taster | **GLM-4-Air** | Nuanced credibility scoring + preference application |
| Feedback | **GLM-4-Air** | Needs to interpret natural language and update config correctly |

---

## Tech Stack

| Concern | Library |
|---|---|
| Agent orchestration | AGNO |
| LLM | `zhipuai` Python SDK |
| Web scraping (static) | `httpx` |
| Web scraping (JS) | `playwright` |
| CLI | `typer` |
| Config | `tomllib` / `tomli-w` |
| Database | `sqlite3` (stdlib) |
| Web UI | `flask` + HTMX |
| Tests | `pytest` |

---

## Error Handling

- **Source failure**: failing source is skipped, others continue. Orchestrator reports failures after run.
- **LLM failure**: article is dropped silently. If LLM fully unavailable, run aborted, user notified on next `newspull`.
- **Preferences corruption**: Feedback agent validates before writing, keeps `preferences.toml.bak` rollback.
- **Empty feed**: clear message with suggested commands.
