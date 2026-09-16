# System Architecture — Spotify Discovery Engine

## 1. System Overview

The **Spotify Discovery Engine** is an end-to-end data ingestion, natural language classification, aggregation, and visualization pipeline designed to analyze Spotify user reviews and surface music discovery frustrations—specifically focusing on the "active explorer" and "lapsed explorer" user segments.

The platform continuously or periodically ingests reviews across multiple channels (Google Play Store, Apple App Store, Reddit, community forums, and social media), normalizes them into a unified PostgreSQL schema on Supabase, classifies each review with an LLM (Groq API using `llama-3.3-70b-versatile` with automatic fallback to `llama-3.1-8b-instant`) against a strict 7-field taxonomy, computes statistical aggregations and crosstabs, and visualizes the results via an interactive Streamlit dashboard.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                      DATA SOURCES                                      │
├──────────────────┬─────────────────┬──────────────────┬───────────────┬────────────────┤
│ Google Play Store│ Apple App Store │  Reddit (Public) │ Forums (Web)  │ Social Media   │
│ (Automated API)  │ (RSS JSON API)  │  (Search JSON)   │ (Manual Paste)│ (Manual Paste) │
└────────┬─────────┴────────┬────────┴────────┬─────────┴───────┬───────┴────────┬───────┘
         │                  │                 │                 │                │
         ▼                  ▼                 ▼                 ▼                ▼
┌──────────────────┬─────────────────┬──────────────────┬────────────────────────────────┐
│ play_store.py    │ app_store.py    │ reddit_public.py │ paste_importer.py              │
│ (live scraper)   │ (RSS ingestor)  │ (public fetcher) │ (paste_sources.txt parser)     │
└────────┬─────────┴────────┬────────┴────────┬─────────┴────────────────┬───────────────┘
         │                  │                 │                          │
         └──────────────────┴────────┬────────┴──────────────────────────┘
                                     ▼
                     ┌───────────────────────────────┐
                     │         SUPABASE (DB)         │
                     │  Table: raw_reviews           │
                     │  - id (PK / source hash)      │
                     │  - source, rating, date, text │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │    CLASSIFIER (Groq Cloud)    │
                     │  classify.py / backend.py     │
                     │  - Primary: llama-3.3-70b     │
                     │  - Fallback: llama-3.1-8b     │
                     │  - 7-field JSON taxonomy      │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │         SUPABASE (DB)         │
                     │  Table: tagged_reviews        │
                     │  - id (PK -> raw_reviews.id)  │
                     │  - 7 taxonomy classification  │
                     └───────────────┬───────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
┌───────────────────────────────────────┐ ┌──────────────────────────────────────────────┐
│           AGGREGATION ENGINE          │ │            STREAMLIT FRONTEND DEMO           │
│  aggregate.py                         │ │  streamlit_app.py                            │
│  - Total & discovery-related counts   │ │  - Tab 1: Live Demo (scrape & classify live) │
│  - Frequency by segment & frustration │ │  - Tab 2: Pipeline Insights (from JSON/live) │
│  - Segment × Frustration crosstab     │ │  - Tab 3: Architecture diagram & stats       │
│  - Top root causes & unmet needs      │ │  - Tab 4: Research Insights (benchmark 456)  │
│  Outputs: insights.json & insights.md │ │  - GitHub Actions trigger & live tracker     │
└──────────────────┬────────────────────┘ └──────────────────────────────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────┐
│          GITHUB ACTIONS CI/CD         │
│  .github/workflows/pipeline.yml       │
│  - Cron: daily 04:30 UTC / 10:00 IST  │
│  - Runs ingest, classify, aggregate   │
│  - Commits updated insights.json      │
└───────────────────────────────────────┘
```

---

## 2. Directory & File Structure

```
spotify-discovery-engine/
├── .github/
│   └── workflows/
│       └── pipeline.yml          # GitHub Actions daily cron & workflow_dispatch pipeline
├── .streamlit/
│   └── secrets.toml.example      # Example secrets for Streamlit Cloud deployment
├── docs/
│   ├── architecture.md           # Original preliminary architectural notes
│   ├── build_brief.md            # Problem specification brief
│   └── problemStatement.md       # Full background problem statement & research guidelines
├── ingestion/
│   ├── app_store.py              # Apple App Store RSS JSON review ingestor
│   ├── paste_importer.py         # Multi-source paste parser for hand-collected reviews
│   ├── play_store.py             # Google Play Store live scraper using google-play-scraper
│   └── reddit_public.py          # Optional Reddit search ingestor via public JSON endpoints
├── .env.example                  # Template for all required environment variables
├── .env                          # Local environment variables (gitignored, secrets protected)
├── .gitignore                    # Git exclusion rules (virtual environments, secrets, caches)
├── ARCHITECTURE.md               # Complete verified system architecture documentation
├── README.md                     # Project overview, quick start, findings, and testing guide
├── aggregate.py                  # Aggregation engine generating insights.json & insights.md
├── backend.py                    # Pure backend helper module for Streamlit & async execution
├── classify.py                   # Groq LLM classification script with retry and backoff
├── classify_backfill.py          # Batch backfill classifier for unclassified database rows
├── init_db.sql                   # Database initialization script (PostgreSQL schema & indexes)
├── insights.json                 # Serialized pipeline statistics and crosstab outputs
├── insights.md                   # Human-readable markdown report of pipeline insights
├── packages.txt                  # OS-level packages for Streamlit Cloud (graphviz)
├── paste_sources.txt             # Hand-collected reviews in "rating | source | text" format
├── requirements.txt              # Python package dependencies
├── streamlit_app.py              # Interactive Streamlit multi-tab dashboard
└── test_db.py                    # Database connection test suite (insert, read, cleanup)
```

---

## 3. Component Details & Workflows

### 3.1 Data Ingestion (`ingestion/`)

1. **Google Play Store (`ingestion/play_store.py`)**:
   - Uses `google-play-scraper` to pull reviews for package `com.spotify.music`.
   - Multi-country scraping across US, IN, GB, CA, AU.
   - Paginates with continuation tokens up to a configurable day cutoff (default 7 days) and review count cap.
   - Deduplicates across regions and upserts to `raw_reviews` using Play Store `reviewId` as primary key.

2. **Paste Importer (`ingestion/paste_importer.py`)**:
   - Parses `paste_sources.txt` containing hand-curated forum, social, and Reddit reviews.
   - Line format: `[rating] | source | text` (where rating is optional for unrated platforms).
   - Generates deterministic, stable SHA-256 IDs based on `hash(source + ":" + text)`.
   - Upserts entries into `raw_reviews`.

3. **Apple App Store (`ingestion/app_store.py`)**:
   - Hits Apple's public RSS customer reviews JSON endpoint for Spotify (`id=324684580`).
   - Cycles through regions (US, GB, CA, AU, IN) up to 10 pages per country.
   - Extracts review ID, star rating, updated timestamp, and content.

4. **Reddit Public Ingestor (`ingestion/reddit_public.py`)**:
   - Targets subreddits `r/spotify` and `r/truespotify` with targeted discovery queries ("discover weekly", "recommendations", "same songs", "discovery").
   - Utilizes public unauthenticated Reddit `.json` endpoints with custom User-Agent headers.

### 3.2 LLM Classification Engine (`classify.py` & `backend.py`)

- **Model Hierarchy**:
  - Primary Model: `llama-3.3-70b-versatile` (high reasoning capability, accurate taxonomy matching).
  - Fallback Model: `llama-3.1-8b-instant` (automatically engaged when token rate limits or quotas are reached).
- **Execution & Safety**:
  - System prompt enforces output format: strictly valid JSON mode (`response_format={"type": "json_object"}`).
  - Strips markdown formatting fences (````json ... ````) defensively before parsing.
  - Detects Groq 429 rate limits, parses dynamic wait periods from error messages, and applies exponential backoff.
  - Queries `raw_reviews` left-joined to `tagged_reviews` to classify only unclassified entries.

### 3.3 Aggregation Engine (`aggregate.py`)

- Fetches all `tagged_reviews` joined with `raw_reviews`.
- Filters for `discovery_related == True` to focus on core discovery pain points.
- Computes:
  - Total volume and percentage of reviews that are discovery-related.
  - Ranked frequency counts for `frustration_type`, `segment`, `desired_behavior`, and `source`.
  - Multi-dimensional crosstab: `segment × frustration_type`.
  - Top 10 `root_cause` and `unmet_need` phrases.
- Produces two deliverables:
  - `insights.json`: Structured JSON for programmatic consumption and the Streamlit dashboard.
  - `insights.md`: Formatted markdown tables for human inspection and reporting.

### 3.4 Interactive Frontend (`streamlit_app.py` & `backend.py`)

Built with Streamlit and Plotly, styled with a dark Spotify theme (`#121212` background, `#1DB954` green accent):
- **Tab 1: Live Demo**:
  - Live scraping of Play Store reviews on demand.
  - Real-time classification via Groq LLM with animated progress indicators and styled review cards.
  - "Trigger Full Pipeline" button using GitHub REST API `workflow_dispatch` with asynchronous status tracking.
- **Tab 2: Pipeline Insights**:
  - Dynamically loads `insights.json`.
  - Visualizes metric KPI cards, frustration horizontal bar chart, segment distribution, segment × frustration heatmap, root causes, unmet needs, and source donut chart.
- **Tab 3: Architecture**:
  - Renders the end-to-end data pipeline diagram using Graphviz.
  - Displays pipeline specifications and repository/prototype links.
- **Tab 4: Research Insights**:
  - Displays the benchmark research dataset (456 reviews collected during the initial research study) that validated the "Discovery Dial" concept.

### 3.5 Automation & CI/CD (`.github/workflows/pipeline.yml`)

- Runs daily at **04:30 UTC / 10:00 AM IST** via cron schedule.
- Supports manual invocation via `workflow_dispatch` with configurable `play_store_days`.
- Workflow stages:
  1. Environment setup (Python 3.11, pip dependencies).
  2. Ingest: Scrapes Play Store & runs paste importer.
  3. Classify: Processes unclassified reviews via Groq (`llama-3.1-8b-instant`).
  4. Aggregate: Computes new insights metrics.
  5. Commit: Pushes updated `insights.json` back to the GitHub repository with `[skip ci]`.

---

## 4. Data Model & Database Schema

The database runs on PostgreSQL (Supabase). Defined in `init_db.sql`:

### Table: `raw_reviews`
Stores normalized, unclassified user feedback from all platforms.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | Unique ID (native ID or SHA-256 hash) |
| `source` | TEXT | NOT NULL, CHECK IN (...) | Source: `play_store`, `app_store`, `reddit`, `forum`, `social` |
| `rating` | INTEGER | CHECK (1 <= rating <= 5) | User rating (nullable for forum/social) |
| `review_date` | TIMESTAMPTZ | NOT NULL | Date review was published |
| `text` | TEXT | NOT NULL | Full text content of the review |
| `scraped_at` | TIMESTAMPTZ | DEFAULT NOW() | Ingestion timestamp |

### Table: `tagged_reviews`
Stores the structured classification generated by the Groq LLM.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY, FK -> `raw_reviews(id)` | References `raw_reviews.id` with CASCADE deletion |
| `frustration_type` | TEXT | NOT NULL, CHECK IN (...) | Frustration taxonomy category |
| `segment` | TEXT | NOT NULL, CHECK IN (...) | Target listener persona category |
| `desired_behavior`| TEXT | NOT NULL, CHECK IN (...) | Desired discovery behavior category |
| `root_cause` | TEXT | NOT NULL | <= 12 words root cause description |
| `unmet_need` | TEXT | NOT NULL | <= 12 words unmet user need |
| `discovery_related`| BOOLEAN| NOT NULL | True if review concerns recommendations/discovery |
| `sentiment` | TEXT | NOT NULL, CHECK IN (...) | `positive`, `neutral`, `negative` |
| `classified_at` | TIMESTAMPTZ | DEFAULT NOW() | Timestamp when LLM processed the record |

---

## 5. Classification Taxonomy

Each review is classified across seven distinct dimensions:

### 1. `frustration_type`
- `stale_recommendations`: Repeated songs/artists in mixes or radio.
- `filter_bubble_lock_in`: Trapped in familiar algorithmic content.
- `discovery_friction`: Difficult to explore or find new music.
- `algorithmic_sameness`: All recommendations feel uniform or predictable.
- `poor_new_release_surfacing`: Inability to discover new tracks by artists.
- `context_blindness`: Recommendations ignore user context/activity.
- `over_personalization`: Excessively narrow suggestions.
- `control_loss`: User lacks steering or reset capability.
- `none`: Not related to music discovery frustrations.

### 2. `segment`
- `lapsed_explorer`: Used to explore actively, now experiences fatigue or repetition.
- `active_explorer`: Continuously and intentionally seeking fresh music.
- `passive_listener`: Content with background music, low discovery intent.
- `genre_loyalist`: Dedicated to specific sub-genres.
- `mood_listener`: Seeks music matching current mood or activity.
- `podcast_first`: Primarily consumes non-music audio.
- `unknown`: Ambiguous or unidentifiable segment.

### 3. `desired_behavior`
- `find_new_artists`
- `break_routine`
- `match_mood_or_context`
- `deep_dive_genre`
- `social_discovery`
- `rediscover_back_catalog`
- `none`

### 4. Supporting Attributes
- `root_cause`: Concise summary phrase (<= 12 words).
- `unmet_need`: Concise summary phrase (<= 12 words).
- `discovery_related`: Boolean flag (`true` or `false`).
- `sentiment`: `positive`, `neutral`, or `negative`.

---

## 6. APIs & External Integrations

| Provider / Target | Protocol / Library | Purpose | Auth / Credentials |
|---|---|---|---|
| **Groq Cloud** | REST API / `groq` Python SDK | LLM classification (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`) | `GROQ_API_KEY` in `.env` |
| **Supabase** | PostgREST / `supabase` Python SDK | Central data storage (`raw_reviews`, `tagged_reviews`) | `SUPABASE_URL`, `SUPABASE_KEY` |
| **Google Play** | HTTPS / `google-play-scraper` | Public review scraping for `com.spotify.music` | None (Public) |
| **Apple App Store**| HTTPS / `requests` | Public customer review RSS feeds | None (Public) |
| **Reddit** | HTTPS / `requests` | Public subreddit search JSON | None (Custom User-Agent) |
| **GitHub Actions** | GitHub REST API v3 | Remote workflow dispatch (`pipeline.yml`) & step status polling | `GITHUB_TOKEN`, `GITHUB_REPO` |

---

## 7. Environment Variables & Security

All sensitive credentials and environment-specific settings are managed via environment variables and loaded with `python-dotenv`:

| Variable Name | Required By | Description | Example / Format |
|---|---|---|---|
| `GROQ_API_KEY` | Classifier, Backend, Streamlit | Groq API authentication key | `gsk_...` |
| `SUPABASE_URL` | All storage modules, Test suite | Supabase project instance URL | `https://xyzcompany.supabase.co` |
| `SUPABASE_KEY` | All storage modules, Test suite | Supabase public anon or service key | `eyJhbGciOi...` |
| `GITHUB_TOKEN` | Streamlit app (Tab 1 dispatch) | Personal access token with repo/workflow scope | `ghp_...` |
| `GITHUB_REPO` | Streamlit app (Tab 1 dispatch) | Target repository path in `owner/repo` format | `user/spotify-discovery-engine` |

> **Security Directives**:
> - `.env` is explicitly listed in `.gitignore` and must never be tracked or pushed to version control.
> - API keys are never printed in logs or included in repository artifacts.
> - Streamlit Cloud deployments utilize `.streamlit/secrets.toml` with the identical keys.

---

## 8. Verification Matrix & Architecture Alignment

The architecture has been verified against the original codebase. The following enhancements and structural alignments are noted:

1. **Orchestration**: While preliminary planning notes mentioned a standalone `weekly_run.py`, the production architecture orchestrates runs via `.github/workflows/pipeline.yml` with step-level status reporting.
2. **Resilience & Fallbacks**: `backend.py` introduces a dynamic fallback mechanism from `llama-3.3-70b-versatile` to `llama-3.1-8b-instant` to handle API rate limits without interrupting UI workflows.
3. **Frontend Architecture**: The UI incorporates 4 distinct tabs (Live Demo, Pipeline Insights, Architecture, and Research Insights) with real-time streaming generators and JavaScript tab switching.
4. **Environment Consistency**: All components read from either `.streamlit/secrets.toml` or `.env` using standard priority chaining (`st.secrets` -> `os.getenv`).
