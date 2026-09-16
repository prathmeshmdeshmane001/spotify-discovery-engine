"""
Phase 3: Classifier
Classifies reviews using Groq LLM and upserts to tagged_reviews table.
"""

import argparse
import os
import json
import time
import re
from dotenv import load_dotenv
from supabase import create_client, Client
from groq import Groq

# Load environment variables
load_dotenv()

# Configuration
PLAY_STORE_SAMPLE_SIZE = 50
BATCH_SIZE = 10
SLEEP_BETWEEN_REQUESTS = 0.5
MAX_RETRIES = 3
RETRY_BACKOFF = 2

# Taxonomy from problem statement
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

def get_reviews_to_classify(limit=None):
    """
    Fetch reviews from raw_reviews that need classification.
    - Uses a LEFT JOIN with tagged_reviews to find only unclassified rows
    - Applies the limit directly in the Supabase query so the database
      never returns more than `limit` rows
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

    supabase: Client = create_client(supabase_url, supabase_key)

    query_limit = limit or PLAY_STORE_SAMPLE_SIZE
    response = (
        supabase.from_("raw_reviews")
        .select("*, tagged_reviews!left(id)")
        .is_("tagged_reviews.id", "null")
        .order("review_date", desc=True)
        .limit(query_limit)
        .execute()
    )
    unclassified = response.data
    print(f"Fetched {len(unclassified)} unclassified reviews from Supabase (limit={query_limit})")

    return unclassified

def classify_review(text, groq_client, model="llama-3.3-70b-versatile"):
    """
    Classify a single review using Groq LLM.
    
    Args:
        text: Review text
        groq_client: Groq client instance
        model: Groq model name to use
    
    Returns:
        Dictionary with classification results, or None if failed
    """
    prompt = f"{TAXONOMY}\n\nReview text:\n{text}\n\nClassification:"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that classifies Spotify reviews according to a fixed taxonomy. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            
            # Strip JSON fences if present
            result_text = re.sub(r'^```json\s*', '', result_text)
            result_text = re.sub(r'^```\s*', '', result_text)
            result_text = re.sub(r'\s*```$', '', result_text)
            
            # Parse JSON
            result = json.loads(result_text)
            
            return result
            
        except Exception as e:
            error_str = str(e)
            
            # Check for token rate limit
            if "rate_limit_exceeded" in error_str and "tokens" in error_str:
                # Extract wait time from error message (e.g., "Please try again in 8m38.4s")
                time_match = re.search(r'Please try again in (\d+m)?(\d+\.?\d*)s?', error_str)
                if time_match:
                    minutes = int(time_match.group(1)[:-1]) if time_match.group(1) else 0
                    seconds = float(time_match.group(2))
                    wait_time = minutes * 60 + seconds
                    print(f"    ⏳ Token rate limit reached. Waiting {wait_time:.0f}s ({minutes}m{seconds:.0f}s)...")
                    time.sleep(wait_time)
                    continue
            
            # Check for 429 rate limit (non-token)
            if "429" in error_str and attempt < MAX_RETRIES - 1:
                print(f"    ⏳ Rate limited (429), backing off {RETRY_BACKOFF}s...")
                time.sleep(RETRY_BACKOFF)
                continue
            
            print(f"    ✗ Classification error: {e}")
            return None
    
    return None

def upsert_tagged_review(review_id, classification, groq_client):
    """
    Upsert a classified review to tagged_reviews table.
    
    Args:
        review_id: Original review ID
        classification: Classification dictionary
        groq_client: Groq client instance (for retry logic)
    
    Returns:
        True if successful, False otherwise
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    tagged_review = {
        "id": review_id,
        "frustration_type": classification.get("frustration_type"),
        "segment": classification.get("segment"),
        "desired_behavior": classification.get("desired_behavior"),
        "root_cause": classification.get("root_cause"),
        "unmet_need": classification.get("unmet_need"),
        "discovery_related": classification.get("discovery_related"),
        "sentiment": classification.get("sentiment")
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            supabase.table("tagged_reviews").upsert(tagged_review, on_conflict="id").execute()
            return True
        except Exception as e:
            if "429" in str(e) and attempt < MAX_RETRIES - 1:
                print(f"    ⏳ Rate limited (429), backing off {RETRY_BACKOFF}s...")
                time.sleep(RETRY_BACKOFF)
                continue
            else:
                print(f"    ✗ Upsert error: {e}")
                return False
    
    return False

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Classify Spotify reviews")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of reviews to classify")
    default_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    parser.add_argument("--model", type=str, default=default_model, help="Groq model to use for classification")
    args = parser.parse_args()

    print("=" * 60)
    print("Phase 3: Classifier")
    print("=" * 60)

    # Initialize Groq client
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY must be set in .env file")

    groq_client = Groq(api_key=groq_api_key)
    model = args.model
    print(f"Using model: {model}")

    # Get reviews to classify
    reviews = get_reviews_to_classify(limit=args.limit)
    
    if not reviews:
        print("\n✗ No reviews to classify")
        return
    
    print(f"\nStarting classification of {len(reviews)} reviews...")
    
    success_count = 0
    failure_count = 0
    
    for i, review in enumerate(reviews, 1):
        print(f"\nClassifying {i}/{len(reviews)}: {review['id'][:20]}...")
        
        # Classify
        classification = classify_review(review['text'], groq_client, model=model)
        
        if not classification:
            print(f"  ✗ Classification failed, skipping")
            failure_count += 1
            time.sleep(SLEEP_BETWEEN_REQUESTS)
            continue
        
        # Upsert
        if upsert_tagged_review(review['id'], classification, groq_client):
            print(f"  ✓ Classified and upserted")
            success_count += 1
        else:
            print(f"  ✗ Upsert failed")
            failure_count += 1
        
        # Progress indicator
        if i % BATCH_SIZE == 0:
            print(f"\nProgress: {i}/{len(reviews)} reviews processed ({success_count} successful, {failure_count} failed)")
        
        # Rate limiting
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    
    print("\n" + "=" * 60)
    print(f"Classification Complete")
    print(f"Total reviews processed: {len(reviews)}")
    print(f"Successfully classified: {success_count}")
    print(f"Failed: {failure_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
