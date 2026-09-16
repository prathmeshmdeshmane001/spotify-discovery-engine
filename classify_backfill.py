"""
One-time backfill classifier for unclassified reviews in Supabase.
Fetches unclassified reviews in batches of 10, classifies them with Groq,
and upserts results to the tagged_reviews table.
"""

import argparse
import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from groq import Groq

# Reuse the classifier logic from classify.py
from classify import TAXONOMY, classify_review, upsert_tagged_review

load_dotenv()

BATCH_SIZE = 10
SLEEP_BETWEEN_REQUESTS = 0.5


def get_supabase_client():
    """Create a Supabase client from environment variables."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    return create_client(supabase_url, supabase_key)


def get_groq_client():
    """Create a Groq client from environment variables."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY must be set in .env file")
    return Groq(api_key=api_key, timeout=30)


def get_unclassified_reviews(supabase, limit=None):
    """
    Fetch reviews from raw_reviews that are not yet in tagged_reviews.
    Returns a list of review dicts sorted by review_date descending.
    """
    # Get IDs of already classified reviews
    classified_response = supabase.table("tagged_reviews").select("id").execute()
    classified_ids = {row["id"] for row in classified_response.data}
    print(f"Found {len(classified_ids)} already classified reviews")

    # Fetch all raw reviews (paginated if needed)
    raw_reviews = []
    page_size = 1000
    offset = 0
    while True:
        response = (
            supabase.table("raw_reviews")
            .select("*")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        batch = response.data
        if not batch:
            break
        raw_reviews.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    print(f"Fetched {len(raw_reviews)} total raw reviews")

    # Filter out already classified
    unclassified = [row for row in raw_reviews if row["id"] not in classified_ids]
    print(f"Found {len(unclassified)} unclassified reviews")

    # Sort by review_date descending so newest are processed first
    unclassified = sorted(unclassified, key=lambda r: r.get("review_date", ""), reverse=True)

    # Apply limit
    if limit and len(unclassified) > limit:
        unclassified = unclassified[:limit]
        print(f"Limiting backfill to {limit} reviews")

    return unclassified


def process_backfill(limit=None):
    """
    Main backfill loop: fetch, classify, and upsert unclassified reviews.
    """
    supabase = get_supabase_client()
    groq_client = get_groq_client()

    reviews = get_unclassified_reviews(supabase, limit=limit)
    if not reviews:
        print("No unclassified reviews to process.")
        return

    total = len(reviews)
    print(f"\nStarting backfill of {total} reviews in batches of {BATCH_SIZE}\n")

    success_count = 0
    fail_count = 0

    for i, review in enumerate(reviews, start=1):
        review_text = review.get("text", "")
        review_id = review.get("id")

        if not review_text:
            print(f"[{i}/{total}] Skipping empty review {review_id}")
            fail_count += 1
            continue

        classification = classify_review(review_text, groq_client)

        if classification:
            tagged = {
                "id": review_id,
                "frustration_type": classification.get("frustration_type"),
                "segment": classification.get("segment"),
                "desired_behavior": classification.get("desired_behavior"),
                "root_cause": classification.get("root_cause"),
                "unmet_need": classification.get("unmet_need"),
                "discovery_related": classification.get("discovery_related"),
                "sentiment": classification.get("sentiment"),
            }
            upsert_tagged_review(review_id, classification, groq_client)
            success_count += 1
        else:
            print(f"[{i}/{total}] Failed to classify review {review_id}")
            fail_count += 1

        # Print progress every 10 reviews
        if i % 10 == 0 or i == total:
            print(f"[{i}/{total}] Progress: {success_count} succeeded, {fail_count} failed")

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print(f"\nBackfill complete: {success_count} succeeded, {fail_count} failed out of {total}")


def main():
    parser = argparse.ArgumentParser(description="Backfill classification for unclassified reviews")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of unclassified reviews to process (default: 50)",
    )
    args = parser.parse_args()

    process_backfill(limit=args.limit)


if __name__ == "__main__":
    main()
