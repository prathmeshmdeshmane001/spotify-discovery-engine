"""
Phase 2a: Play Store Ingestor
Scrapes reviews from Google Play Store for com.spotify.music and upserts to Supabase.
"""

import argparse
import os
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from google_play_scraper import Sort, reviews

# Load environment variables
load_dotenv()

MAX_REVIEWS_PER_RUN = 100


def scrape_play_store_reviews(app_id="com.spotify.music", days=7, lang="en", countries=["us", "in", "gb", "ca", "au"], max_reviews=MAX_REVIEWS_PER_RUN):
    """
    Scrape reviews from Google Play Store within the last N days.
    Pages through reviews using continuation tokens until date threshold is reached.
    Scrapes from multiple countries and combines results.
    
    Args:
        app_id: Google Play Store app ID
        days: Number of days to look back (default: 7)
        lang: Language code (default: 'en' for English)
        countries: List of country codes to scrape from (default: ['us', 'in', 'gb', 'ca', 'au'])
        max_reviews: Hard cap on total reviews to return (default: MAX_REVIEWS_PER_RUN)
    
    Returns:
        List of review dictionaries (raw from google_play-scraper)
    """
    cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    all_reviews = []
    seen_ids = set()  # Avoid duplicates across countries (unique by review ID)
    
    print(f"Scraping reviews from Google Play Store for app: {app_id}")
    print(f"Language: {lang}")
    print(f"Countries: {', '.join(countries)}")
    print(f"Date cutoff: {cutoff_date.isoformat()}")
    
    for country in countries:
        print(f"\nScraping from country: {country.upper()}")
        country_reviews = []
        continuation_token = None
        page_count = 0
        earliest_date = None
        latest_date = None
        
        while True:
            try:
                # Fetch a batch of reviews
                result, continuation_token = reviews(
                    app_id,
                    lang=lang,
                    country=country,
                    sort=Sort.NEWEST,
                    count=200,  # Batch size
                    continuation_token=continuation_token
                )
                
                page_count += 1
                
                # Filter reviews by date and deduplicate across countries.
                # Reviews are sorted newest-first, so the first old review means we can stop.
                batch_filtered = []
                duplicate_count = 0
                old_review_count = 0
                hit_cutoff = False
                for review in result:
                    review_id = str(review["reviewId"])
                    review_date = review["at"]
                    
                    # Track date range
                    if earliest_date is None or review_date < earliest_date:
                        earliest_date = review_date
                    if latest_date is None or review_date > latest_date:
                        latest_date = review_date
                    
                    # Check if review is within date window first
                    if review_date < cutoff_date:
                        old_review_count += 1
                        hit_cutoff = True
                        break
                    
                    # Skip if we've already seen this review (cross-country dedup)
                    if review_id in seen_ids:
                        duplicate_count += 1
                        continue
                    
                    seen_ids.add(review_id)
                    batch_filtered.append(review)
                
                # Debug logging for first page of each country
                if page_count == 1 and (duplicate_count > 0 or old_review_count > 0):
                    print(f"    Debug: {duplicate_count} duplicates, {old_review_count} old reviews in this batch")
                
                country_reviews.extend(batch_filtered)
                all_reviews.extend(batch_filtered)
                print(f"  Page {page_count}: {len(batch_filtered)} new reviews (country: {len(country_reviews)}, total: {len(all_reviews)})")

                # Stop if we have enough reviews for the demo
                if max_reviews and len(all_reviews) >= max_reviews:
                    print(f"  Reached max_reviews limit ({max_reviews})")
                    break
                
                # Stop if no more reviews available
                if not continuation_token:
                    print(f"  No more reviews available for {country.upper()}")
                    break
                
                # Stop if we hit the date cutoff in this batch (reviews are newest-first)
                if hit_cutoff or len(batch_filtered) == 0:
                    print(f"  No more reviews within {days}-day window for {country.upper()}")
                    break
                
                # Polite rate limiting between batches
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ERROR scraping batch for {country.upper()}: {e}")
                break
        
        # Log summary for this country
        date_range_str = ""
        if earliest_date and latest_date:
            date_range_str = f" (date range: {earliest_date.isoformat()} to {latest_date.isoformat()})"
        print(f"OK Completed {country.upper()}: {len(country_reviews)} reviews across {page_count} pages{date_range_str}")

        # Stop moving to next country if we already have enough reviews
        if max_reviews and len(all_reviews) >= max_reviews:
            break
    
    print(f"\nOK Total unique reviews across all countries: {len(all_reviews)}")
    print(f"OK Reviews within {days}-day window: {len(all_reviews)}")
    
    return all_reviews

def normalize_review(review):
    """
    Normalize a Play Store review to raw_reviews schema.
    
    Args:
        review: Raw review from google_play-scraper
    
    Returns:
        Dictionary matching raw_reviews schema
    """
    return {
        "id": str(review["reviewId"]),
        "source": "play_store",
        "rating": review["score"],
        "review_date": review["at"].isoformat(),
        "text": review["content"]
    }

def upsert_reviews_to_supabase(reviews):
    """
    Upsert reviews to Supabase raw_reviews table.
    Uses review ID as primary key to prevent duplicates.
    
    Args:
        reviews: List of normalized review dictionaries
    
    Returns:
        Tuple of (success_count, failure_count)
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    success_count = 0
    failure_count = 0
    
    print(f"\nUpserting {len(reviews)} reviews to Supabase...")
    
    for i, review in enumerate(reviews, 1):
        try:
            # Upsert using review ID as primary key
            supabase.table("raw_reviews").upsert(review, on_conflict="id").execute()
            success_count += 1
            
            # Progress indicator
            if i % 50 == 0:
                print(f"  Progress: {i}/{len(reviews)} reviews upserted")
            
            # Polite rate limiting
            time.sleep(0.05)
            
        except Exception as e:
            failure_count += 1
            print(f"  ERROR Failed to upsert review {review['id']}: {e}")
    
    print(f"\nOK Upsert complete: {success_count} successful, {failure_count} failed")
    return success_count, failure_count

def main(days=7, max_reviews=MAX_REVIEWS_PER_RUN):
    """Main execution function."""
    print("=" * 60)
    print("Phase 2a: Play Store Ingestor")
    print("=" * 60)
    
    # Scrape reviews from last N days, multiple countries, capped at max_reviews
    raw_reviews = scrape_play_store_reviews(days=days, lang="en", countries=["us", "in", "gb", "ca", "au"], max_reviews=max_reviews)
    
    if not raw_reviews:
        print("\nERROR No reviews scraped. Exiting.")
        return
    
    # Normalize reviews
    print("\nNormalizing reviews to raw_reviews schema...")
    normalized_reviews = [normalize_review(review) for review in raw_reviews]
    print(f"OK Normalized {len(normalized_reviews)} reviews")
    
    # Upsert to Supabase
    success_count, failure_count = upsert_reviews_to_supabase(normalized_reviews)
    
    print("\n" + "=" * 60)
    print(f"Phase 2a Complete")
    print(f"Total reviews processed: {len(normalized_reviews)}")
    print(f"Successfully upserted: {success_count}")
    print(f"Failed: {failure_count}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--max-reviews", type=int, default=MAX_REVIEWS_PER_RUN)
    args = parser.parse_args()
    main(days=args.days, max_reviews=args.max_reviews)
