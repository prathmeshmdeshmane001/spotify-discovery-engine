# Problem Statement: Spotify Meaningful Discovery — Review Analysis Engine + AI-Native MVP

## Project decisions (locked — read first)
- Product chosen: **Spotify**
- Part 1 approach: **classification engine**, NOT retrieval/RAG. Every review is
  tagged against a fixed discovery taxonomy and counted. The deliverable is
  defensible frequencies and crosstabs (e.g. "filter-bubble lock-in: 20 mentions",
  "lapsed explorers most affected"), not a generated summary.
- Part 4 approach: a deployed **AI-native MVP** (agent / RAG) — this is where
  retrieval and generation belong.
- Stack: scrapers (App Store, Play Store, Reddit, optional forums) → Supabase →
  Groq (llama-3.3-70b-versatile) classifier → aggregation → insights.json /
  insights.md. Optional weekly refresh via GitHub Actions.
- Deadline: 6 July 2026, 3:59:00 PM IST. Hard cutoff.

## Overview
The objective of this project is to increase **meaningful music discovery** on
Spotify and reduce repetitive listening. Spotify has acquired millions of users
and built one of the world's most sophisticated recommendation systems, yet a
significant share of listening still comes from repeat playlists, familiar
artists, and previously discovered tracks. As a Product Manager on the Growth
Team, the goal is to understand why, validate it with users, and ship an
AI-native MVP that addresses the root cause.

## Objective
Design and implement, in four parts:
1. An AI-powered **review analysis engine** that classifies user feedback at
   scale and surfaces discovery pain points with frequency counts.
2. **Primary user research** (5–6 interviews) validating the chosen segment.
3. A clearly framed **problem definition** (root cause, target segment, business
   case).
4. A deployed **AI-native MVP** that demonstrates why AI is uniquely suited to
   solving the discovery problem.

## Target Users
- Spotify listeners whose discovery has declined over time ("Lapsed Explorers" —
  the primary focus segment).
- Secondarily: active explorers, passive/background listeners, genre loyalists.

## Scope of Work

### Part 1 — Review Analysis Engine (classification, not retrieval)
- Ingest user feedback from: App Store reviews, Play Store reviews, Reddit
  discussions, community forums, and social media conversations. (App stores and
  Reddit are primary; forums/social are optional and fragile.)
- Normalize every review to a single schema: id, source, rating, date, text.
- Classify **every** review with an LLM against a fixed taxonomy:
  - frustration_type: stale_recommendations | filter_bubble_lock_in |
    discovery_friction | algorithmic_sameness | poor_new_release_surfacing |
    context_blindness | over_personalization | control_loss | none
  - segment: lapsed_explorer | active_explorer | passive_listener |
    genre_loyalist | mood_listener | podcast_first | unknown
  - desired_behavior: find_new_artists | break_routine | match_mood_or_context |
    deep_dive_genre | social_discovery | rediscover_back_catalog | none
  - plus: root_cause (<=12 words), unmet_need (<=12 words),
    discovery_related (bool), sentiment (positive|neutral|negative)
- Aggregate into: total vs discovery-related %, counts by frustration_type,
  segment, desired_behavior, source; a segment × frustration_type crosstab; and
  top root_cause / unmet_need phrases by frequency.
- The engine must help answer:
  - Why do users struggle to discover new music?
  - What are the most common frustrations with recommendations?
  - What listening behaviors are users trying to achieve?
  - What causes users to repeatedly listen to the same content?
  - Which user segments experience different discovery challenges?
  - What unmet needs emerge consistently across reviews?

### Part 2 — User Research
- Pick the segment surfaced by Part 1 (Lapsed Explorers).
- Screen and conduct 5–6 semi-structured interviews.
- Synthesize into patterns; validate or challenge the AI insights; document the
  root cause in one sentence.

### Part 3 — Problem Definition
- Articulate: root cause, target user segment, and why solving it makes business
  sense (discovery → saves, session depth, retention; reduced churn).

### Part 4 — AI-Native MVP (deployed to production)
- Build and deploy a functional MVP: a feature prototype or an agent.
- Must demonstrate why AI is uniquely suited, explaining:
  - Why traditional recommendation systems are insufficient.
  - What AI unlocks that was previously difficult.
  - How AI changes the user experience.

## Constraints

### Data and Sources
- Use publicly available reviews/discussions only. Do not scrape anything behind
  a login or in violation of a platform's terms of service.
- For Part 1, prioritize a working classification over raw volume. A clean,
  well-reasoned sample beats a broken large scrape.

### Methodology
- Part 1 must produce **verifiable counts**, not a retrieved-and-summarized
  paragraph. Do not pre-filter reviews by hand to favor a hypothesis; ingest a
  broad set and let the classifier judge discovery-relevance consistently.

### Privacy and Security
- Do not collect, store, or process any personally identifiable information from
  reviewers (names, handles tied to identity, emails, etc.) beyond what is needed
  for analysis. Keep all API keys in a .env file, never hard-coded.

### Deck Constraints (strictly enforced)
- The Fellow's name must NOT appear anywhere in the deck.
- 10 slides maximum (title slide counts as one).
- Each slide title states the slide's key message, not a generic label.
- Background/text must be readable and colorblind-safe (avoid red/green pairings).
- Supporting artefacts hyperlinked, with view access granted to the reader.
- File < 40 MB; named like "NL Spotify".
- Minimum font size 14 (Google Slides / PPT).

## Expected Deliverables
1. **Review Analysis Workflow** — a link to test the workflow, plus a 1-slider
   inside the deck outlining how it works.
2. **10-slide deck (PDF)** outlining the thought process across all four parts.
3. **Deployed MVP** — a link to the live prototype or agent.

## Success Criteria
- Part 1 produces defensible, source-backed counts and a clear segment×frustration
  story that answers the six required questions.
- Part 2 interviews validate or meaningfully refine the AI insights.
- Part 3 states a sharp root cause, segment, and business case.
- Part 4 MVP is live, demonstrates AI's unique fit, and ties back to the root cause.
- Deck meets every formatting constraint.

## Summary
Build a trustworthy, evidence-driven analysis of why Spotify's Lapsed Explorers
stop discovering, validate it with real users, and ship an AI-native MVP that
breaks the repeat-listening loop in a way traditional recommenders cannot. The
project prioritizes verifiable insight (counts, crosstabs, real interviews) over
volume or polish, and a deployed product that demonstrably uses AI's unique
strengths — natural-language intent, explained recommendations, and tunable
novelty.