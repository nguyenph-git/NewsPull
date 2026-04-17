# Graph Report - .  (2026-04-15)

## Corpus Check
- Corpus is ~14,025 words - fits in a single context window. You may not need a graph.

## Summary
- 290 nodes · 422 edges · 36 communities detected
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 82 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Feedback & Preferences|Feedback & Preferences]]
- [[_COMMUNITY_Orchestrator & Sources|Orchestrator & Sources]]
- [[_COMMUNITY_Gatherer & Source Protocol|Gatherer & Source Protocol]]
- [[_COMMUNITY_Config & Source Contracts|Config & Source Contracts]]
- [[_COMMUNITY_Concepts & Test Fixtures|Concepts & Test Fixtures]]
- [[_COMMUNITY_CLI Commands & Display|CLI Commands & Display]]
- [[_COMMUNITY_Digester & DB Write|Digester & DB Write]]
- [[_COMMUNITY_SQLite DB Layer|SQLite DB Layer]]
- [[_COMMUNITY_Source Abstraction & Resilience|Source Abstraction & Resilience]]
- [[_COMMUNITY_CLI Integration Tests|CLI Integration Tests]]
- [[_COMMUNITY_DB Unit Tests|DB Unit Tests]]
- [[_COMMUNITY_Source Unit Tests|Source Unit Tests]]
- [[_COMMUNITY_Web Endpoint Tests|Web Endpoint Tests]]
- [[_COMMUNITY_Feedback & Deep-Merge Tests|Feedback & Deep-Merge Tests]]
- [[_COMMUNITY_Orchestrator Tests|Orchestrator Tests]]
- [[_COMMUNITY_DigesterAgent Core|DigesterAgent Core]]
- [[_COMMUNITY_Shared Test Fixtures|Shared Test Fixtures]]
- [[_COMMUNITY_Config Unit Tests|Config Unit Tests]]
- [[_COMMUNITY_Taster Unit Tests|Taster Unit Tests]]
- [[_COMMUNITY_Architecture Docs|Architecture Docs]]
- [[_COMMUNITY_Digester Unit Tests|Digester Unit Tests]]
- [[_COMMUNITY_API Test Script|API Test Script]]
- [[_COMMUNITY_Data Model Tests|Data Model Tests]]
- [[_COMMUNITY_Model Fixture Alignment|Model Fixture Alignment]]
- [[_COMMUNITY_In-Memory Pipeline Design|In-Memory Pipeline Design]]
- [[_COMMUNITY_Flask App Factory|Flask App Factory]]
- [[_COMMUNITY_Digester Test Coverage|Digester Test Coverage]]
- [[_COMMUNITY_LLM Model Docs|LLM Model Docs]]
- [[_COMMUNITY_Package Init (agents)|Package Init (agents)]]
- [[_COMMUNITY_Package Init (sources)|Package Init (sources)]]
- [[_COMMUNITY_Package Init (cli)|Package Init (cli)]]
- [[_COMMUNITY_Package Init (web)|Package Init (web)]]
- [[_COMMUNITY_Package Init (tests)|Package Init (tests)]]
- [[_COMMUNITY_Prefs Backup Restore|Prefs Backup Restore]]
- [[_COMMUNITY_Deep-Merge Tests|Deep-Merge Tests]]
- [[_COMMUNITY_Web Mark-Read Test|Web Mark-Read Test]]

## God Nodes (most connected - your core abstractions)
1. `OrchestratorAgent` - 22 edges
2. `RawArticle` - 16 edges
3. `FeedbackAgent` - 15 edges
4. `GathererAgent` - 12 edges
5. `Source` - 11 edges
6. `RankedArticle` - 9 edges
7. `TasterAgent` - 9 edges
8. `DigesterAgent` - 9 edges
9. `Run full pipeline. Returns (articles_saved, error_messages).` - 9 edges
10. `RSSSource` - 8 edges

## Surprising Connections (you probably didn't know these)
- `SQLite Storage Schema (Design Spec)` --references--> `DB Initialization Table Tests`  [INFERRED]
  docs/superpowers/specs/2026-04-15-newspull-design.md → tests/test_db.py
- `Web View Design (Design Spec)` --references--> `Web Index Endpoint Tests`  [INFERRED]
  docs/superpowers/specs/2026-04-15-newspull-design.md → tests/test_web.py
- `Source Failure Resilience Concept` --references--> `FailingSource Test Stub`  [INFERRED]
  README.md → tests/test_gatherer.py
- `Config Preferences Tests` --references--> `Global Preferences TOML Schema (Design Spec)`  [INFERRED]
  tests/test_config.py → docs/superpowers/specs/2026-04-15-newspull-design.md
- `CLI Commands Reference (README)` --references--> `CLI Command Tests`  [INFERRED]
  README.md → tests/test_cli.py

## Hyperedges (group relationships)
- **Gather-Digest-Taste-Save Pipeline Flow** — gatherer_gathereragent, digester_digesteragent, taster_tasteragent, db_savearticle [EXTRACTED 0.98]
- **Article Data Model Transformation Chain** — models_rawarticle, models_summarizedarticle, models_rankedarticle [EXTRACTED 0.97]
- **CLI and Web Both Invoke Orchestrator and Feedback Agents** — cli_fetch, webapp_fetch_route, orchestrator_orchestratoragent, cli_feedback, webapp_review_route, feedback_feedbackagent [INFERRED 0.88]
- **Shared Test Fixture Infrastructure** — conftest_tmp_db_path_fixture, conftest_tmp_prefs_path_fixture, conftest_default_prefs_fixture, conftest_sample_raw_article_fixture, conftest_sample_ranked_article_fixture [EXTRACTED 1.00]
- **Pipeline Stage Test Coverage** — test_gatherer_fetch_all, test_digester_digest, test_taster_taste, test_orchestrator_pipeline [INFERRED 0.90]
- **Design Spec, Implementation Plan, and README Alignment** — spec_agent_responsibilities, plan_file_map, readme_5_agent_architecture [INFERRED 0.88]

## Communities

### Community 0 - "Feedback & Preferences"
Cohesion: 0.12
Nodes (22): load_prefs Function, save_prefs Function, deep_merge(), FeedbackAgent, config_add_source(), config_remove_source(), config_set_weight(), feedback() (+14 more)

### Community 1 - "Orchestrator & Sources"
Cohesion: 0.13
Nodes (11): fetch CLI Command, HackerNewsSource, OrchestratorAgent, Run full pipeline. Returns (articles_saved, error_messages)., Multi-Agent News Pipeline, RedditSource, RSSSource, Source (+3 more)

### Community 2 - "Gatherer & Source Protocol"
Cohesion: 0.16
Nodes (16): ABC, Source, GathererAgent, Fetch from all sources in parallel. Returns (articles, error_messages)., RawArticle, OrchestratorAgent._build_sources Method, Source Base Class, HackerNewsSource Class (+8 more)

### Community 3 - "Config & Source Contracts"
Cohesion: 0.16
Nodes (2): load_prefs(), save_prefs()

### Community 4 - "Concepts & Test Fixtures"
Cohesion: 0.12
Nodes (21): Credibility Scoring Concept, Natural Language Preference Adaptation Concept, default_prefs pytest Fixture, tmp_db_path pytest Fixture, tmp_prefs_path pytest Fixture, CLI Commands Reference (README), Global Preferences TOML Schema (Design Spec), SQLite Storage Schema (Design Spec) (+13 more)

### Community 5 - "CLI Commands & Display"
Cohesion: 0.18
Nodes (17): feedback CLI Command, pull CLI Command, _render_feed Helper, _review_prompt Helper, show_feed CLI Command, web CLI Command, count_cross_refs Function, get_backlog_articles Function (+9 more)

### Community 6 - "Digester & DB Write"
Cohesion: 0.16
Nodes (15): DEFAULT_PREFS (topics/sources/credibility/digester), save_article Function, DigesterAgent.digest Method, DigesterAgent.digest_all Method, Semaphore(8) Concurrency Limit, deep_merge Function, FeedbackAgent.process Method, GathererAgent.fetch_all Method (+7 more)

### Community 7 - "SQLite DB Layer"
Cohesion: 0.28
Nodes (12): count_cross_refs(), get_backlog_articles(), get_connection(), get_unread_articles(), init_db(), mark_articles_read(), Count existing articles with the same URL (cross-reference detection)., Highest-ranked unread articles. (+4 more)

### Community 8 - "Source Abstraction & Resilience"
Cohesion: 0.18
Nodes (12): Source Abstract Base Class, Source.fetch() Abstract Method, Source Failure Resilience Concept, Error Handling Strategy (README), Error Handling Design Rationale (Design Spec), FailingSource Test Stub, GathererAgent fetch_all Tests, GoodSource Test Stub (+4 more)

### Community 9 - "CLI Integration Tests"
Cohesion: 0.22
Nodes (3): make_db_article(), test_default_command_shows_feed(), test_pull_command_shows_backlog()

### Community 10 - "DB Unit Tests"
Cohesion: 0.33
Nodes (7): make_article(), test_count_cross_refs_increments(), test_get_backlog_returns_oldest_first(), test_get_unread_articles(), test_mark_articles_read(), test_save_article_returns_id(), test_save_duplicate_url_returns_none()

### Community 11 - "Source Unit Tests"
Cohesion: 0.2
Nodes (0): 

### Community 12 - "Web Endpoint Tests"
Cohesion: 0.29
Nodes (2): make_db_article(), test_index_returns_200()

### Community 13 - "Feedback & Deep-Merge Tests"
Cohesion: 0.33
Nodes (2): make_llm_response(), test_feedback_agent_updates_prefs()

### Community 14 - "Orchestrator Tests"
Cohesion: 0.57
Nodes (5): make_ranked(), make_raw(), make_summary(), test_orchestrator_reports_source_errors(), test_orchestrator_run_saves_articles()

### Community 15 - "DigesterAgent Core"
Cohesion: 0.33
Nodes (4): DigesterAgent, main Function (test-api), test_model Function, ZhipuAI API Client (test-api)

### Community 16 - "Shared Test Fixtures"
Cohesion: 0.33
Nodes (0): 

### Community 17 - "Config Unit Tests"
Cohesion: 0.33
Nodes (0): 

### Community 18 - "Taster Unit Tests"
Cohesion: 0.6
Nodes (5): make_summary(), test_taste_all_processes_batch(), test_taste_boosts_matching_topic(), test_taste_filters_low_credibility(), test_taste_returns_ranked_article()

### Community 19 - "Architecture Docs"
Cohesion: 0.33
Nodes (6): Implementation File Map (Plan), Task 1: Project Scaffolding (Plan), 5-Agent Architecture (README), Supported Sources Table (README), Agent Responsibility Table (Design Spec), Tech Stack Table (Design Spec)

### Community 20 - "Digester Unit Tests"
Cohesion: 0.6
Nodes (3): make_llm_response(), test_digest_all_filters_none_results(), test_digest_returns_summarized_article()

### Community 21 - "API Test Script"
Cohesion: 0.67
Nodes (3): main(), Test if a specific model works, test_model()

### Community 22 - "Data Model Tests"
Cohesion: 0.5
Nodes (0): 

### Community 23 - "Model Fixture Alignment"
Cohesion: 0.67
Nodes (3): sample_ranked_article pytest Fixture, sample_raw_article pytest Fixture, Data Model Field Tests

### Community 24 - "In-Memory Pipeline Design"
Cohesion: 0.67
Nodes (3): In-Memory Intermediate Pipeline Concept, In-Memory Data Pipeline (README), Parallel Execution Design Rationale

### Community 25 - "Flask App Factory"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Digester Test Coverage"
Cohesion: 1.0
Nodes (2): DigesterAgent digest Tests, DigesterAgent digest_all Tests

### Community 27 - "LLM Model Docs"
Cohesion: 1.0
Nodes (2): LLM Model Selection Table (README), LLM Model Selection Rationale (Design Spec)

### Community 28 - "Package Init (agents)"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Package Init (sources)"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Package Init (cli)"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Package Init (web)"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Package Init (tests)"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Prefs Backup Restore"
Cohesion: 1.0
Nodes (1): restore_prefs_backup Function

### Community 34 - "Deep-Merge Tests"
Cohesion: 1.0
Nodes (1): deep_merge Function Tests

### Community 35 - "Web Mark-Read Test"
Cohesion: 1.0
Nodes (1): Web Mark-Read Endpoint Test

## Knowledge Gaps
- **36 isolated node(s):** `Test if a specific model works`, `ZhipuAI API Client (test-api)`, `SQLite DB Schema (articles + feed_history)`, `restore_prefs_backup Function`, `/mark-read Route` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Flask App Factory`** (2 nodes): `create_app()`, `app.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Digester Test Coverage`** (2 nodes): `DigesterAgent digest Tests`, `DigesterAgent digest_all Tests`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `LLM Model Docs`** (2 nodes): `LLM Model Selection Table (README)`, `LLM Model Selection Rationale (Design Spec)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init (agents)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init (sources)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init (cli)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init (web)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init (tests)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Prefs Backup Restore`** (1 nodes): `restore_prefs_backup Function`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Deep-Merge Tests`** (1 nodes): `deep_merge Function Tests`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Web Mark-Read Test`** (1 nodes): `Web Mark-Read Endpoint Test`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `OrchestratorAgent` connect `Orchestrator & Sources` to `Feedback & Preferences`, `Gatherer & Source Protocol`, `Config & Source Contracts`, `SQLite DB Layer`, `DigesterAgent Core`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `RawArticle` connect `Gatherer & Source Protocol` to `Orchestrator & Sources`, `Config & Source Contracts`, `Digester & DB Write`, `DigesterAgent Core`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `RankedArticle` connect `SQLite DB Layer` to `Orchestrator & Sources`, `Config & Source Contracts`, `Digester & DB Write`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `OrchestratorAgent` (e.g. with `GathererAgent` and `DigesterAgent`) actually correct?**
  _`OrchestratorAgent` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `RawArticle` (e.g. with `Fetch from all sources in parallel. Returns (articles, error_messages).` and `DigesterAgent`) actually correct?**
  _`RawArticle` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `FeedbackAgent` (e.g. with `Show your ranked news feed. All shown stories are marked read.` and `Dig into backlog — fetched but not yet displayed articles.`) actually correct?**
  _`FeedbackAgent` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `GathererAgent` (e.g. with `Source` and `OrchestratorAgent`) actually correct?**
  _`GathererAgent` has 5 INFERRED edges - model-reasoned connections that need verification._