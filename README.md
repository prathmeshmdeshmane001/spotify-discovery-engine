# Spotify Discovery Engine — Review Analysis Pipeline

> NextLeap Cohort 42 · Spotify Discovery Dial Feature Concept · July 2026

An end-to-end pipeline that ingests Spotify user reviews from multiple sources, classifies them using Groq LLM, and surfaces insights about music discovery frustrations — specifically targeting the active explorer segment.

---

## Live Demo

| Link | What it shows |
|---|---|
| [Live Pipeline Demo](https://spotify-discovery-engine-icedwrwrsufiahmd2st5fs.streamlit.app/) | Test the workflow — scrape, classify, insights |
| [Discovery Dial Prototype](https://discovery-dial-mu.vercel.app) | The feature concept built from these findings |

---

## What This Pipeline Does
Data Sources → Ingest → Classify → Segment → Aggregate → Insights

1. **Ingest** — Scrapes Google Play Store reviews live (`play_store.py`) and imports hand-collected App Store, Reddit, forum, and social reviews (`paste_importer.py`)
2. **Classify** — Sends each review to Groq LLM (llama-3.3-70b-versatile) and classifies against a fixed 7-field taxonomy
3. **Segment** — Each review gets: `frustration_type` · `segment` · `desired_behavior` · `root_cause` · `unmet_need` · `discovery_related` · `sentiment`
4. **Aggregate** — `aggregate.py` produces ranked counts, crosstabs, and top findings → `insights.json`
5. **Schedule** — GitHub Actions runs the full pipeline daily at 10:00 AM IST (04:30 UTC)

---

## Key Findings — June 2026 Research Run

| Metric | Value |
|---|---|
| Total reviews classified | 456 |
| Discovery-related | 159 (34.9%) |
| Dominant segment | active_explorer (113 reviews) |
| Top frustration | stale_recommendations (65 reviews) |
| Top unmet need | "new music" (36 reviews) |
| Key crosstab | active_explorer + stale_recommendations = 53 reviews |

These findings directly drove the Discovery Dial feature concept — a playlist-level novelty dial with per-track AI reasoning built in React + Vite + Groq.

---

## Sources

| Source | Reviews | Method |
|---|---|---|
| Google Play Store | 353 | Live scraper (automated) |
| Forums | 42 | Hand collected |
| Social (Twitter/X) | 33 | Hand collected |
| Reddit (r/spotify) | 18 | Hand collected |
| App Store | 10 | Hand collected |

---

## Project Structure
```
spotify-discovery-engine/
├── ingestion/
│   ├── play_store.py        # Live Play Store scraper
│   └── paste_importer.py    # Multi-source paste importer
├── classify.py              # Groq LLM classifier
├── aggregate.py             # Insights aggregator
├── streamlit_app.py         # Live demo app
├── insights.json            # Latest pipeline output
├── insights.md              # Human-readable findings
├── paste_sources.txt        # Hand-collected reviews
├── .github/
│   └── workflows/
│       └── pipeline.yml     # GitHub Actions scheduler
└── docs/
    ├── architecture.md      # Phase-wise architecture
    └── edge_cases.md        # Edge case handling
```

---

## How to Test the Workflow

**Option 1 — Streamlit app (easiest, recommended):**
Open [Live Pipeline Demo](https://spotify-discovery-engine-icedwrwrsufiahmd2st5fs.streamlit.app/) → Tab 1 → Click "Classify 5 Fresh Reviews" → Watch the pipeline classify real Spotify reviews in real time → See session insights.

**Option 2 — GitHub Actions (full pipeline):**
Go to [Actions tab](https://github.com/pbehuray/spotify-discovery-engine/actions) → pipeline.yml → Run workflow → Watch all 5 steps run automatically in the logs.

**Option 3 — Local run:**
```bash
git clone https://github.com/pbehuray/spotify-discovery-engine
cd spotify-discovery-engine
pip install -r requirements.txt
# Add GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY to .env
python ingestion/play_store.py --days 7 --max-reviews 100
python ingestion/paste_importer.py
python classify.py --limit 50
python aggregate.py
streamlit run streamlit_app.py
```

---

## How to Run Locally

**1. Clone and install:**
```bash
git clone https://github.com/pbehuray/spotify-discovery-engine
pip install -r requirements.txt
```

**2. Set environment variables:**
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Fill in GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY
```

**3. Run full pipeline:**
```bash
python ingestion/play_store.py --days 7 --max-reviews 100
python ingestion/paste_importer.py
python classify.py --limit 50
python aggregate.py
```

**4. Run Streamlit demo:**
```bash
streamlit run streamlit_app.py
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Ingestion | Python · google-play-scraper |
| Storage | Supabase (Postgres) |
| Classification | Groq API · llama-3.3-70b-versatile |
| Aggregation | Python · pandas |
| Scheduler | GitHub Actions (cron 04:30 UTC daily) |
| Demo UI | Streamlit |
| Prototype | React · Vite · Vercel · Groq |

---

## Scheduler

Runs automatically every day at **10:00 AM IST (04:30 UTC)** via GitHub Actions:
- Scrapes up to 100 new Play Store reviews (7-day window)
- Classifies up to 50 unclassified reviews via Groq
- Regenerates insights.json
- Commits updated insights back to repo

Manual trigger available via `workflow_dispatch` in the Actions tab.

---

## Related

- **Discovery Dial Prototype** — [discovery-dial-mu.vercel.app](https://discovery-dial-mu.vercel.app)
- **Discovery Dial Repo** — [github.com/pbehuray/discovery-dial](https://github.com/pbehuray/discovery-dial)
- **NextLeap Cohort 42** — Spotify feature concept · July 2026

---

*Research dataset: 456 reviews · 6 sources · June 2026. Pipeline continues running daily via GitHub Actions.*