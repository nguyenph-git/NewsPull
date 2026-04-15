# NewsPull

A personal news aggregation and AI summarization system that automatically gathers content from multiple sources, distills it into concise bullet-point summaries, verifies credibility, and presents a ranked feed that adapts to your evolving preferences.

## Features

- **On-demand CLI feed** — Get your news when you want it, not daily digests
- **Optional web UI** — Clean, dark-themed interface with HTMX
- **5-agent architecture** — Parallel processing for fast content pulls
- **Credibility scoring** — Cross-reference detection and source reputation
- **Natural language feedback** — Tune your feed without editing config files
- **Multiple sources** — RSS feeds, HackerNews, Reddit, YouTube

## Quick Start

**Fastest way to get started** (one command):

```bash
# Clone and install
git clone https://github.com/your-username/NewsPull.git
cd NewsPull
pip install -e ".[dev]"

# Set API key
export ZHIPUAI_API_KEY="your-api-key"

# Run newspull
./run                    # Show latest feed
./run fetch               # Fetch new content
./run web                 # Start web UI
```

The `./run` script checks for your API key and provides helpful setup instructions if missing.

---

## Architecture

NewsPull uses a 5-agent AGNO architecture:

| Agent | Responsibility |
|--------|-------------|
| **Orchestrator** | Coordinates the pipeline, spawns other agents in parallel |
| **Gatherer** | Fetches raw content from multiple sources simultaneously |
| **Digester** | Summarizes articles using GLM-4-Flash (fast, cost-effective) |
| **Taster** | Scores credibility and ranks articles based on your preferences using GLM-4-Air |
| **Feedback** | Interprets natural language feedback to update your preferences using GLM-4-Air |

**Data pipeline:**
```
Gatherer (parallel) → [raw, in-memory] → Digester (parallel) → [summary, in-memory] → Taster (parallel) → SQLite
```

Raw articles are never persisted to disk — only final ranked articles are stored.

## Installation

### Prerequisites

- Python 3.11 or later
- ZhipuAI API key (for GLM-4 models)

### Install

```bash
# Clone the repository
git clone https://github.com/your-username/NewsPull.git
cd NewsPull

# Install in development mode
pip install -e ".[dev]"

# Install Playwright browsers (for JavaScript-heavy sources)
playwright install chromium
```

### Dependencies

- **agno** — Agent orchestration framework
- **zhipuai** — ZhipuAI GLM models (GLM-4-Flash, GLM-4-Air)
- **httpx** — HTTP client for static sources
- **playwright** — Browser automation for JS-heavy sources (Reddit, YouTube)
- **typer** — CLI framework
- **rich** — Terminal rendering
- **flask** — Web UI
- **feedparser** — RSS/Atom feed parsing

## Configuration

### API Key

Set your ZhipuAI API key as an environment variable:

```bash
export ZHIPUAI_API_KEY="your-api-key-here"
```

For persistent configuration, add to your shell profile (`.zshrc`, `.bashrc`):

```bash
echo 'export ZHIPUAI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Preferences

Preferences are stored in `~/.newspull/preferences.toml`. The file is created automatically on first run.

Default structure:
```toml
[topics]
ai = 1.0
tech = 0.8
politics = 0.3

[sources]
reddit = ["r/MachineLearning", "r/technology"]
youtube = []
rss = []
hn = true

[credibility]
min_score = 0.5
cross_ref_bonus = 0.2

[digester]
style = "concise"
keypoints = 5
```

You can edit this file manually or use the CLI config commands (see below).

## Usage

### CLI Commands

**Show latest feed** (marks all shown articles as read, prompts for review)
```bash
newspull
```

**Show backlog** (articles that were fetched but not yet displayed)
```bash
newspull pull
```

**Fetch fresh content** (runs the full agent pipeline)
```bash
newspull fetch
```

**Provide feedback** (directly invoke feedback agent)
```bash
newspull feedback
```

**Start web UI** (opens browser on http://localhost:5001)
```bash
newspull web
# Custom port
newspull web --port 8080
```

**Config commands**
```bash
# Add a source
newspull config add-source reddit r/Python

# Remove a source
newspull config remove-source reddit r/MachineLearning

# Set topic weight
newspull config set-weight topic ai 0.9

# Set digester preference
newspull config set-weight digester style simple
```

### Review Prompt

After viewing your feed (via `newspull` or `newspull pull`), you'll be prompted:

```
Do you want to leave a review? [y/N]: y

Type your review below:
> the language used was too complex, please dumb it down and add more keypoints

✓ Got it — preferences updated.
```

The feedback agent interprets your natural language input and updates `~/.newspull/preferences.toml` accordingly.

### Example Feed Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[#1] GPT-5 released with reasoning improvements  ★ 0.92  · 3 sources
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • OpenAI announced GPT-5 with improved chain-of-thought reasoning
  • Benchmarks show 40% improvement on MATH and coding tasks
  • Available via API immediately, ChatGPT rollout next week
  • Priced same as GPT-4o
  · r/Machinelearning · HackerNews · TheVerge

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[#2] New AI model for code generation  ★ 0.87
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Anthropic releases Claude 4 with improved coding capabilities
  • Benchmarks show 30% faster generation vs Claude 3.5
  • Supports 200k token context window
  · HackerNews

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Do you want to leave a review? [y/N]:
```

## Web UI

Start the web server:
```bash
newspull web
```

Features:
- **Feed display** — Articles with credibility scores and cross-reference counts
- **Automatic mark-as-read** — All displayed articles are marked when page loads
- **Fetch button** — Trigger agent pipeline from the web UI
- **Review box** — Provide natural language feedback without leaving the CLI
- **Responsive dark theme** — Clean, readable interface

## Sources

### Supported Sources

| Source | Description | Notes |
|---------|-------------|-------|
| **RSS** | Standard RSS/Atom feeds | Any RSS URL |
| **HackerNews** | HackerNews front page | No config required |
| **Reddit** | Subreddit top posts (last 24 hours) | Add subreddits via config |
| **YouTube** | Channel videos (RSS/Atom feed) | Add channel IDs via config |

### Adding Sources

**RSS feeds:**
```bash
newspull config add-source rss https://example.com/feed.xml
```

**Reddit subreddits:**
```bash
newspull config add-source reddit r/artificial
newspull config add-source reddit r/technology
```

**YouTube channels:**
```bash
newspull config add-source youtube UCXXXXXXXXXXXXXXXX
# Get channel ID from channel URL
```

## Development

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_orchestrator.py -v

# With coverage
pytest tests/ --cov=newspull --cov-report=html
```

### Project Structure

```
newspull/
├── agents/           # 5 agent implementations
│   ├── orchestrator.py  # Pipeline coordinator
│   ├── gatherer.py     # Parallel source fetching
│   ├── digester.py     # GLM-4-Flash summarization
│   ├── taster.py       # GLM-4-Air credibility scoring
│   └── feedback.py     # Natural language preferences
├── sources/          # Source implementations
│   ├── base.py         # Source abstraction
│   ├── rss.py          # RSS feeds
│   ├── hn.py           # HackerNews API
│   ├── reddit.py       # Reddit API
│   └── youtube.py      # YouTube Atom feeds
├── cli/              # CLI interface (typer)
├── web/              # Web UI (Flask + HTMX)
│   ├── app.py          # Flask application
│   └── templates/      # HTML templates
├── db.py             # SQLite database layer
├── config.py          # Preferences management
└── models.py          # Data models
```

## Error Handling

- **Source failure**: If a source fails, others continue. Errors are reported at the end of the run.
- **LLM failure**: Articles with LLM errors are dropped silently. If the LLM is completely unavailable, the run is aborted.
- **Preferences corruption**: Feedback agent validates before writing and keeps `preferences.toml.bak` for rollback.
- **Empty feed**: Clear message with suggested commands.

## Performance

- **Parallel fetching**: Multiple sources are fetched simultaneously
- **Batch processing**: Digesting and tasting agents process articles in parallel batches
- **In-memory pipeline**: Raw articles never hit disk, only final ranked articles are stored
- **SQLite indexed**: Fast queries on URLs and timestamps

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
