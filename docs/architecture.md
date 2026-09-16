# Architecture — Spotify Review Analysis Engine

This document outlines the system architecture for the Spotify Review Analysis Engine (Part 1). The system is designed as a classification pipeline that ingests reviews, tags them against a fixed taxonomy, and produces verifiable frequency counts and crosstabs.

## System Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Data Sources  │────▶│   Supabase DB   │────▶│   Classifier    │
│                 │     │                 │     │   (Groq LLM)    │
│ • Play Store    │     │ • raw_reviews   │     │                 │
│ • App Store     │     │ • tagged_reviews│────▶│   Aggregation   │
│ • Reddit        │     │                 │     │                 │
│ • Forums/Social │     └─────────────────┘     └─────────────────┘
└─────────────────┘                                         │
                                                               ▼
                                                      ┌─────────────────┐
                                                      │   Insights      │
                                                      │ • JSON export   │
                                                      │ • Markdown      │
                                                      └─────────────────┘
```

## Technology Stack

- **Language**: Python 3.11+
- **Database**: Supabase (PostgreSQL)
- **LLM Provider**: Groq (llama-3.3-70b-versatile)
- **Package Management**: pip + requirements.txt
- **Secrets Management**: python-dotenv (.env file)
- **Scraping**: google-play-scraper, app-store-scraper

## Data Model

### Table: `raw_reviews`
Stores normalized review data from all sources.

| Column | Type | Description |
|--------|------|-------------|
| `id` | text (PK) | Stable unique ID from source |
| `source` | text | 'play_store' \| 'app_store' \| 'reddit' \| 'forum' \| 'social' |
| `rating` | int (nullable) | 1-5 where available, null for reddit/forum/social |
| `review_date` | timestamptz | Original review date |
| `text` | text | Review content |
| `scraped_at` | timestamptz | Timestamp when scraped (default now()) |

### Table: `tagged_reviews`
Stores LLM classifications for each review.

| Column | Type | Description |
|--------|------|-------------|
| `id` | text (PK, FK) | References raw_reviews.id |
| `frustration_type` | text | From taxonomy (e.g., stale_recommendations, none) |
| `segment` | text | From taxonomy (e.g., lapsed_explorer, unknown) |
| `desired_behavior` | text | From taxonomy (e.g., find_new_artists, none) |
| `root_cause` | text | <= 12 words |
| `unmet_need` | text | <= 12 words |
| `discovery_related` | boolean | Whether review is about discovery/recommendations |
| `sentiment` | text | 'positive' \| 'neutral' \| 'negative' |
| `classified_at` | timestamptz | Timestamp when classified (default now()) |

## Classification Taxonomy

### Frustration Types
- `stale_recommendations` - Same songs/artists repeatedly
- `filter_bubble_lock_in` - Trapped in familiar content
- `discovery_friction` - Hard to find new music
- `algorithmic_sameness` - Recommendations feel identical
- `poor_new_release_surfacing` - New releases not shown
- `context_blindness` - Ignores mood/context
- `over_personalization` - Too narrow recommendations
- `control_loss` - User lacks control
- `none` - Not about discovery

### Segments
- `lapsed_explorer` - Used to discover, now stuck
- `active_explorer` - Still actively discovering
- `passive_listener` - Background listening
- `genre_loyalist` - Stays in one genre
- `mood_listener` - Music for context/mood
- `podcast_first` - Podcast-focused
- `unknown` - Cannot determine

### Desired Behaviors
- `find_new_artists` - Want to discover new artists
- `break_routine` - Want to escape repetitive listening
- `match_mood_or_context` - Music for specific situations
- `deep_dive_genre` - Explore within a genre
- `social_discovery` - Discover through others
- `rediscover_back_catalog` - Revisit forgotten music
- `none` - No specific discovery goal

## Phase-by-Phase Architecture

### Phase 1: Foundation
- Project skeleton with virtual environment
- Supabase connection via supabase-py client
- Database schema creation (raw_reviews, tagged_reviews)
- Basic connectivity test (insert/read dummy row)

### Phase 2: Ingestion
- **Play Store Ingestor**: google-play-scraper → raw_reviews
- **App Store Ingestor**: app-store-scraper → raw_reviews
- **Paste Importer**: paste_sources.txt → raw_reviews (reddit/forum/social)
- Idempotent upserts using source IDs as primary keys
- Rate limiting and error isolation per source

### Phase 3: Classification
- Batch processor reads unclassified rows from raw_reviews
- For each review: calls Groq API with taxonomy prompt
- Uses Groq JSON mode for reliable parsing
- Defensive JSON parsing (strip fences, log failures)
- Upserts results to tagged_reviews
- Progress logging and rate limit handling

### Phase 4: Aggregation
- SQL query over tagged_reviews WHERE discovery_related = true
- Computes: total vs discovery-related %, counts by taxonomy fields
- Generates segment × frustration_type crosstab
- Extracts top root_cause and unmet_need phrases
- Exports to insights.json and insights.md

### Phase 5: Weekly Refresh (Optional)
- weekly_run.py orchestrates: scrape → classify → aggregate
- Only processes recent reviews (incremental)
- GitHub Actions cron workflow for automation
- Idempotent and safe to re-run

## Key Design Principles

1. **Classification, not retrieval**: Every review is tagged and counted. No vector database or embeddings in Part 1.
2. **Idempotent operations**: All upserts use source IDs as primary keys; re-running is safe.
3. **Error isolation**: One failing source never kills the pipeline; each wrapped in try/except.
4. **Verifiable outputs**: Frequency counts and crosstabs, not generated summaries.
5. **Secrets management**: All API keys in .env, never hard-coded.
6. **Incremental processing**: Phase 5 only processes new data, not full re-scrapes.

## Folder Structure

```
spotify-discovery/
  docs/
    problemStatement.md
    build_brief.md
    architecture.md
  ingestion/
    play_store.py
    app_store.py
    paste_importer.py
  paste_sources.txt
  classify.py
  aggregate.py
  weekly_run.py
  test_db.py
  .env
  .gitignore
  requirements.txt
  README.md
```

## Security Considerations

- No PII stored beyond what's publicly available
- All API keys in .env (gitignored)
- Supabase uses new sb_secret_... format keys
- No scraping behind login walls or violating ToS
- Rate limiting on all external API calls

## Phase 5: Streamlit Frontend Demo

A lightweight web dashboard that demonstrates the pipeline in real time.

### Tab 1: Live Ingestion
- Scrape latest Play Store reviews on demand
- Classify newly scraped reviews via Groq in real time
- Display results as review cards with source, rating, taxonomy tags, and sentiment
- Button to trigger full pipeline via GitHub Actions (`workflow_dispatch`)

### Tab 2: Pipeline Insights
- Load `insights.json` and render charts:
  - Frustration types (bar chart)
  - Segment distribution (pie/donut chart)
  - Segment × frustration heatmap
  - Source breakdown
  - Top root causes (bar chart)
  - Top unmet needs (bar chart)

### Tab 3: Architecture
- Graphviz flow diagram showing the full pipeline
- Links to GitHub repo and live prototype

### Design
- Dark theme
- Spotify green (`#1DB954`) accent color

## Phase 6: GitHub Actions Scheduler

Automated daily refresh that runs the entire pipeline in CI/CD.

### Schedule
- Cron: `30 4 * * *` (10:00 AM IST = 04:30 UTC daily)
- `workflow_dispatch` enabled for manual testing

### Workflow Steps
1. Checkout repository
2. Set up Python
3. Install dependencies
4. Set secrets as environment variables
   - `GROQ_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
5. Run Play Store scraper
6. Run classifier
7. Run aggregator
8. Commit updated `insights.json` and `insights.md` back to the repo

### Logging
- Each step prints start/end status and key counts
- Scraper logs reviews fetched
- Classifier logs how many reviews were classified and any failures
- Aggregator logs total classified and discovery-related counts

### Security
- Secrets stored as GitHub repository secrets
- No secrets logged to output
- `insights.json` and `insights.md` are committed so results are visible without re-running the pipeline
