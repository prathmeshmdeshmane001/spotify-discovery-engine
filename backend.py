"""
Streamlit backend — pure functions for the Spotify Discovery dashboard.
No UI here; imported by the Streamlit frontend.
"""

import os
import json
import time
import re
import requests
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client

load_dotenv()


# Lazy import ingestion.play_store to avoid import failures at app startup
# on Streamlit Cloud if the scraper package has platform issues.
_PLAY_STORE = None


def _get_play_store():
    global _PLAY_STORE
    if _PLAY_STORE is None:
        from ingestion.play_store import (
            scrape_play_store_reviews,
            normalize_review,
            upsert_reviews_to_supabase,
        )

        _PLAY_STORE = {
            "scrape_play_store_reviews": scrape_play_store_reviews,
            "normalize_review": normalize_review,
            "upsert_reviews_to_supabase": upsert_reviews_to_supabase,
        }
    return _PLAY_STORE


def _get_secret(key):
    """Read from st.secrets first, then fall back to environment variables."""
    try:
        value = st.secrets.get(key)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(key)


# Reuse the classification taxonomy from classify.py
TAXONOMY = """
You are classifying Spotify user reviews about music discovery. Classify each review according to this taxonomy:

frustration_type (must be one of):
- stale_recommendations: Same songs/artists repeated in recommendations
- filter_bubble_lock_in: Trapped in familiar content, unable to discover new music
- discovery_friction: Difficulty finding new music, poor discovery features
- algorithmic_sameness: All recommendations feel the same, predictable
- poor_new_release_surfacing: New releases not surfaced well
- context_blindness: Recommendations ignore context (time, mood, activity)
- over_personalization: Too personalized, no variety or exploration
- control_loss: User has no control over what's recommended
- none: Not related to discovery frustration

segment (must be one of):
- lapsed_explorer: Used to discover new music but stopped
- active_explorer: Still actively seeking new music
- passive_listener: Background listening, not seeking discovery
- genre_loyalist: Stays within specific genres
- mood_listener: Listens based on mood/context
- podcast_first: Primarily listens to podcasts
- unknown: Cannot determine segment

desired_behavior (must be one of):
- find_new_artists: Wants to discover new artists
- break_routine: Wants variety from usual listening
- match_mood_or_context: Wants music matching situation/mood
- deep_dive_genre: Wants to explore a specific genre deeply
- social_discovery: Wants music shared by friends/social
- rediscover_back_catalog: Wants to find old/forgotten music
- none: No specific desired behavior

Additional fields:
- root_cause: Brief explanation in 12 words or fewer
- unmet_need: Brief explanation in 12 words or fewer
- discovery_related: true if the review is about music discovery/recommendations, false otherwise
- sentiment: positive, neutral, or negative

Return ONLY valid JSON with these exact keys:
{
  "frustration_type": "...",
  "segment": "...",
  "desired_behavior": "...",
  "root_cause": "...",
  "unmet_need": "...",
  "discovery_related": true/false,
  "sentiment": "positive/neutral/negative"
}
"""

MAX_RETRIES = 3
SLEEP_BETWEEN_REQUESTS = 0.5
RETRY_BACKOFF = 2

# Production classifier model
GROQ_MODEL = _get_secret("GROQ_MODEL") or "openai/gpt-oss-20b"
# Fallback model used silently when the production model hits rate limits
GROQ_FALLBACK_MODEL = _get_secret("GROQ_FALLBACK_MODEL") or "openai/gpt-oss-20b"


def _get_groq_client():
    """Initialize Groq client from st.secrets or env."""
    api_key = _get_secret("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in st.secrets or environment")
    return Groq(api_key=api_key, timeout=30)


def _get_supabase_client():
    """Initialize Supabase client from st.secrets or env."""
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in st.secrets or environment")
    return create_client(url, key)


def _classify_with_model(text, model, groq_client):
    """
    Internal helper: classify a review with a specific Groq model.

    Returns:
        (classification_dict, error_str) tuple
    """
    prompt = f"{TAXONOMY}\n\nReview text:\n{text}\n\nClassification:"

    for attempt in range(MAX_RETRIES):
        try:
            response = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that classifies Spotify reviews according to a fixed taxonomy. Return ONLY valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
                max_tokens=1000,
                timeout=30,
            )

            result_text = response.choices[0].message.content

            # Strip JSON fences if present
            result_text = re.sub(r"^```json\s*", "", result_text)
            result_text = re.sub(r"^```\s*", "", result_text)
            result_text = re.sub(r"\s*```$", "", result_text)

            return json.loads(result_text), None

        except Exception as e:
            error_str = str(e)

            if "rate_limit_exceeded" in error_str and "tokens" in error_str:
                # Don't wait; signal caller to try fallback model
                return None, error_str

            if "429" in error_str and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF)
                continue

            return None, error_str

    return None, "max retries exceeded"


def classify_single_review(text):
    """
    Classify a single raw review text using Groq.
    Tries the production model first; silently falls back to a faster model
    if Groq rate limits are hit.

    Args:
        text: Raw review text

    Returns:
        Classification dict, or None if classification failed
    """
    groq_client = _get_groq_client()

    # Try production model first
    result, error = _classify_with_model(text, GROQ_MODEL, groq_client)
    if result is not None:
        print(f"Classified with {GROQ_MODEL}")
        return result

    # If rate limited or model not found, silently fall back
    if error and ("rate_limit_exceeded" in error or "model_not_found" in error or "404" in error):
        fallback = GROQ_FALLBACK_MODEL if GROQ_FALLBACK_MODEL != GROQ_MODEL else "openai/gpt-oss-20b"
        print(f"Issue with {GROQ_MODEL} ({error}), falling back to {fallback}")
        result, _ = _classify_with_model(text, fallback, groq_client)
        if result is not None:
            print(f"Classified with {fallback}")
            return result
        # Also try other available chat model if both failed
        for alt_model in ["openai/gpt-oss-20b", "groq/compound-mini", "llama-3.1-8b-instant"]:
            if alt_model not in (GROQ_MODEL, fallback):
                res, _ = _classify_with_model(text, alt_model, groq_client)
                if res is not None:
                    print(f"Classified with {alt_model}")
                    return res

    print(f"Classification error: {error}")
    return None


def run_live_ingestion(n=10):
    """
    Scrape latest Play Store reviews (7 days), classify them, and upsert to DB.

    Args:
        n: Maximum number of newly scraped reviews to classify and return

    Returns:
        List of dicts with review_text, rating, segment, frustration_type,
        discovery_related, sentiment
    """
    return list(run_live_demo(n=n))


def run_live_demo(n=5):
    """
    Generator that scrapes the most recent Play Store reviews and classifies
    them one by one, yielding a result dict after each successful classification.

    Args:
        n: Maximum number of most recent reviews to classify

    Yields:
        Dict with review_text, rating, segment, frustration_type,
        discovery_related, sentiment
    """
    play_store = _get_play_store()
    scrape_play_store_reviews = play_store["scrape_play_store_reviews"]
    normalize_review = play_store["normalize_review"]
    upsert_reviews_to_supabase = play_store["upsert_reviews_to_supabase"]

    print("Starting live demo ingestion...")

    # Scrape only US for a fast demo, stop after 20 reviews so filtering leaves enough
    raw_reviews = scrape_play_store_reviews(app_id="com.spotify.music", days=30, countries=["us"], max_reviews=20)
    if not raw_reviews:
        print("No reviews scraped.")
        return

    # Sort by review date descending, keep only substantive reviews, then take n
    raw_reviews = sorted(raw_reviews, key=lambda r: r["at"], reverse=True)
    reviews = [r for r in raw_reviews if len(r.get("content", "")) > 50][:n]
    normalized = [normalize_review(r) for r in reviews]
    print(f"Normalized {len(normalized)} most recent substantive reviews")

    # Optionally upsert raw reviews to Supabase
    try:
        upsert_reviews_to_supabase(normalized)
    except Exception as e:
        print(f"Upsert raw reviews failed: {e}")

    for review in normalized:
        classification = classify_single_review(review["text"])
        if not classification:
            continue

        # Upsert classified tag to Supabase
        try:
            supabase = _get_supabase_client()
            tagged = {
                "id": review["id"],
                "frustration_type": classification.get("frustration_type"),
                "segment": classification.get("segment"),
                "desired_behavior": classification.get("desired_behavior"),
                "root_cause": classification.get("root_cause"),
                "unmet_need": classification.get("unmet_need"),
                "discovery_related": classification.get("discovery_related"),
                "sentiment": classification.get("sentiment"),
            }
            supabase.table("tagged_reviews").upsert(tagged, on_conflict="id").execute()
        except Exception as e:
            print(f"Upsert tagged review failed: {e}")

        yield {
            "review_text": review["text"],
            "rating": review["rating"],
            "segment": classification.get("segment"),
            "frustration_type": classification.get("frustration_type"),
            "discovery_related": classification.get("discovery_related"),
            "sentiment": classification.get("sentiment"),
        }

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print(f"Live demo complete")


def get_live_stats():
    """
    Query Supabase for live pipeline stats after classification.

    Returns:
        Dict with total_reviews, discovery_related_count, top_segments,
        latest_segment, and last_classified_at
    """
    supabase = _get_supabase_client()

    # Total raw reviews ingested
    total_resp = supabase.table("raw_reviews").select("id", count="exact").execute()
    total_reviews = total_resp.count or 0

    # Discovery-related classified reviews
    discovery_resp = (
        supabase.table("tagged_reviews")
        .select("id", count="exact")
        .eq("discovery_related", True)
        .execute()
    )
    discovery_count = discovery_resp.count or 0

    # Top 3 segments by count
    segments_resp = supabase.table("tagged_reviews").select("segment").execute()
    segment_counts = {}
    for row in segments_resp.data:
        seg = row.get("segment", "unknown")
        segment_counts[seg] = segment_counts.get(seg, 0) + 1
    top_segments = sorted(segment_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    # Most recent segment and classification timestamp
    latest_resp = (
        supabase.table("tagged_reviews")
        .select("segment, classified_at")
        .order("classified_at", desc=True)
        .limit(1)
        .execute()
    )
    latest_segment = None
    last_classified_at = None
    if latest_resp.data:
        latest_segment = latest_resp.data[0].get("segment")
        last_classified_at = latest_resp.data[0].get("classified_at")

    return {
        "total_reviews": total_reviews,
        "discovery_related_count": discovery_count,
        "top_segments": top_segments,
        "latest_segment": latest_segment,
        "last_classified_at": last_classified_at,
    }


def trigger_github_actions():
    """
    Trigger the GitHub Actions workflow_dispatch for pipeline.yml.

    Returns:
        True if triggered successfully, False otherwise
    """
    token = _get_secret("GITHUB_TOKEN")
    repo = _parse_repo()

    if not token:
        raise ValueError("GITHUB_TOKEN not found in st.secrets or environment")

    url = f"https://api.github.com/repos/{repo}/actions/workflows/pipeline.yml/dispatches"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {"ref": "main"}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        return response.status_code in (204, 200)
    except Exception as e:
        print(f"Failed to trigger GitHub Actions: {e}")
        return False


def trigger_full_pipeline():
    """
    Trigger the GitHub Actions workflow_dispatch for pipeline.yml.
    Returns the new run_id if found, True if triggered but run_id not found,
    or False if dispatch failed.
    """
    token = _get_secret("GITHUB_TOKEN")
    repo = _parse_repo()

    if not token:
        raise ValueError("GITHUB_TOKEN not found in st.secrets or environment")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Get latest run_id BEFORE dispatch so we can detect the new one
    try:
        runs_url = f"https://api.github.com/repos/{repo}/actions/workflows/pipeline.yml/runs?per_page=1"
        pre_resp = requests.get(runs_url, headers=headers, timeout=30)
        pre_resp.raise_for_status()
        pre_runs = pre_resp.json().get("workflow_runs", [])
        pre_run_id = pre_runs[0]["id"] if pre_runs else None
    except Exception:
        pre_run_id = None

    # Dispatch
    dispatch_url = f"https://api.github.com/repos/{repo}/actions/workflows/pipeline.yml/dispatches"
    try:
        resp = requests.post(dispatch_url, headers=headers, json={"ref": "main"}, timeout=30)
        if resp.status_code not in (204, 200):
            return False
    except Exception as e:
        print(f"Failed to trigger GitHub Actions: {e}")
        return False

    # Poll up to 20s for the new run to appear
    import time as _t
    for _ in range(10):
        _t.sleep(2)
        try:
            post_resp = requests.get(runs_url, headers=headers, timeout=30)
            post_resp.raise_for_status()
            post_runs = post_resp.json().get("workflow_runs", [])
            if post_runs and post_runs[0]["id"] != pre_run_id:
                return post_runs[0]["id"]
        except Exception:
            pass

    return True  # dispatched but couldn't capture run_id


def _parse_repo():
    """Parse owner/repo from st.secrets or env GITHUB_REPO."""
    repo = _get_secret("GITHUB_REPO")
    if not repo:
        return "prathmeshmdeshmane001/spotify-discovery-engine"
    return repo.strip()


def load_insights():
    """
    Load insights dynamically from Supabase (live) if credentials are available,
    and fallback to insights.json.
    """
    try:
        supabase = _get_supabase_client()
        response = (
            supabase.table("tagged_reviews")
            .select("*, raw_reviews(source, rating, review_date, text)")
            .execute()
        )
        if response.data and len(response.data) > 0:
            from aggregate import calculate_insights
            insights = calculate_insights(response.data)
            insights["source_type"] = "live_database"
            return insights
    except Exception as e:
        print(f"Live insights fetch failed, falling back to insights.json: {e}")

    project_root = os.path.dirname(os.path.abspath(__file__))
    insights_path = os.path.join(project_root, "insights.json")
    try:
        with open(insights_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["source_type"] = "cached_file"
            return data
    except Exception as e:
        print(f"Failed to read insights.json: {e}")
        return {}


def get_recent_tagged_reviews(limit=50):
    """
    Fetch the most recent classified reviews with full taxonomy metadata.
    """
    try:
        supabase = _get_supabase_client()
        response = (
            supabase.table("tagged_reviews")
            .select("*, raw_reviews(source, rating, review_date, text)")
            .order("id", desc=True)
            .limit(limit)
            .execute()
        )
        reviews = []
        for r in response.data or []:
            raw = r.get("raw_reviews") or {}
            reviews.append({
                "id": r.get("id"),
                "text": raw.get("text", ""),
                "rating": raw.get("rating", 0),
                "source": raw.get("source", "play_store"),
                "review_date": raw.get("review_date", ""),
                "segment": r.get("segment", "unknown"),
                "frustration_type": r.get("frustration_type", "none"),
                "desired_behavior": r.get("desired_behavior", "none"),
                "root_cause": r.get("root_cause", ""),
                "unmet_need": r.get("unmet_need", ""),
                "discovery_related": r.get("discovery_related", False),
                "sentiment": r.get("sentiment", "neutral"),
            })
        return reviews
    except Exception as e:
        print(f"Error fetching recent tagged reviews: {e}")
        return []


def get_pipeline_run_status():
    """
    Get the latest workflow run status for pipeline.yml.

    Returns:
        Status string: "queued", "in_progress", "completed", or "failed"
    """
    token = _get_secret("GITHUB_TOKEN")
    repo = _parse_repo()

    if not token:
        raise ValueError("GITHUB_TOKEN not found in st.secrets or environment")

    url = f"https://api.github.com/repos/{repo}/actions/workflows/pipeline.yml/runs?per_page=1"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        runs = data.get("workflow_runs", [])
        if not runs:
            return "unknown"

        latest = runs[0]
        status = latest.get("status")
        conclusion = latest.get("conclusion")

        if status == "queued":
            return "queued"
        if status == "in_progress":
            return "in_progress"
        if status == "completed":
            return conclusion if conclusion else "completed"
        return status

    except Exception as e:
        print(f"Failed to get pipeline status: {e}")
        return "unknown"


def get_pipeline_step_status(run_id=None):
    """
    Get the active pipeline stage by inspecting GitHub Actions job steps.

    Returns a dict:
      {
        "run_status": "queued" | "in_progress" | "completed" | "failed" | "unknown",
        "active_stage": 0-4,   # 0=pending/queued, 1=ingestion, 2=classification,
                                # 3=aggregation, 4=complete
        "stages": [            # list of 4 stage dicts
          {"name": str, "state": "pending" | "active" | "complete"}
        ]
      }
    """
    token = _get_secret("GITHUB_TOKEN")
    repo = _parse_repo()

    stage_names = ["Ingestion", "Classification", "Aggregation", "Insights Ready"]
    pending_stages = [{"name": n, "state": "pending"} for n in stage_names]

    if not token:
        return {"run_status": "unknown", "active_stage": 0, "stages": pending_stages}

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        # 1. Get the specific run (by run_id if provided, else latest)
        if run_id and isinstance(run_id, int):
            run_url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}"
            run_resp = requests.get(run_url, headers=headers, timeout=30)
            run_resp.raise_for_status()
            latest = run_resp.json()
        else:
            runs_url = f"https://api.github.com/repos/{repo}/actions/workflows/pipeline.yml/runs?per_page=1"
            runs_resp = requests.get(runs_url, headers=headers, timeout=30)
            runs_resp.raise_for_status()
            runs = runs_resp.json().get("workflow_runs", [])
            if not runs:
                return {"run_status": "unknown", "active_stage": 0, "stages": pending_stages}
            latest = runs[0]

        run_status = latest.get("status", "unknown")
        run_conclusion = latest.get("conclusion")
        run_id = latest.get("id")

        if run_status == "queued":
            return {"run_status": "queued", "active_stage": 0, "stages": pending_stages}

        if run_status == "completed" and run_conclusion != "success":
            stages = [{"name": n, "state": "complete"} for n in stage_names]
            return {"run_status": run_conclusion or "completed", "active_stage": 4, "stages": stages}

        # 2. Get job steps
        jobs_url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs"
        jobs_resp = requests.get(jobs_url, headers=headers, timeout=30)
        jobs_resp.raise_for_status()
        jobs = jobs_resp.json().get("jobs", [])

        step_names = []
        for job in jobs:
            for step in job.get("steps", []):
                step_names.append((step.get("name", ""), step.get("status", ""), step.get("conclusion", "")))

        def step_done(keyword):
            for name, status, conclusion in step_names:
                if keyword.lower() in name.lower() and status == "completed":
                    return True
            return False

        def step_running(keyword):
            for name, status, conclusion in step_names:
                if keyword.lower() in name.lower() and status == "in_progress":
                    return True
            return False

        # Map steps → stages (matches actual step names in pipeline.yml)
        ingestion_done = step_done("run play store scraper") or step_done("run paste importer")
        classification_done = step_done("classify unclassified reviews")
        aggregation_done = step_done("aggregate insights") or step_done("commit updated insights")

        ingestion_active = step_running("run play store scraper") or step_running("run paste importer")
        classification_active = step_running("classify unclassified reviews")
        aggregation_active = step_running("aggregate insights") or step_running("commit updated insights")

        if run_status == "completed" and run_conclusion == "success":
            stages = [{"name": n, "state": "complete"} for n in stage_names]
            return {"run_status": "completed", "active_stage": 4, "stages": stages}

        # Build stage states
        stages = []
        active_stage = 1

        if ingestion_done:
            stages.append({"name": "Ingestion", "state": "complete"})
            active_stage = 2
        elif ingestion_active:
            stages.append({"name": "Ingestion", "state": "active"})
            active_stage = 1
        else:
            stages.append({"name": "Ingestion", "state": "active"})
            active_stage = 1

        if classification_done:
            stages.append({"name": "Classification", "state": "complete"})
            active_stage = 3
        elif classification_active or (ingestion_done and not classification_done):
            stages.append({"name": "Classification", "state": "active" if ingestion_done else "pending"})
            if ingestion_done:
                active_stage = 2
        else:
            stages.append({"name": "Classification", "state": "pending"})

        if aggregation_done:
            stages.append({"name": "Aggregation", "state": "complete"})
            active_stage = 4
        elif aggregation_active or (classification_done and not aggregation_done):
            stages.append({"name": "Aggregation", "state": "active" if classification_done else "pending"})
            if classification_done:
                active_stage = 3
        else:
            stages.append({"name": "Aggregation", "state": "pending"})

        if aggregation_done:
            stages.append({"name": "Insights Ready", "state": "complete"})
            active_stage = 4
        else:
            stages.append({"name": "Insights Ready", "state": "pending"})

        return {"run_status": run_status, "active_stage": active_stage, "stages": stages}

    except Exception as e:
        print(f"Failed to get pipeline step status: {e}")
        return {"run_status": "unknown", "active_stage": 0, "stages": pending_stages}
