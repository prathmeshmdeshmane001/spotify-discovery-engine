"""
Phase 2b: App Store Ingestor
Scrapes reviews from Apple App Store RSS JSON endpoint for Spotify (app id 324684580) and upserts to Supabase.
"""

import os
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def scrape_app_store_reviews(app_id="324684580", days=90, countries=["us", "gb", "ca", "au", "in"], max_pages=10):
    """
    Scrape reviews from Apple App Store RSS JSON endpoint within the last N days.
    Scrapes from multiple countries and combines results.
    
    Args:
        app_id: Apple App Store app ID
        days: Number of days to look back (default: 90)
        countries: List of country codes to scrape from (default: ['us', 'gb', 'ca', 'au', 'in'])
        max_pages: Maximum pages to fetch per country (default: 10)
    
    Returns:
        List of review dictionaries normalized to raw_reviews schema
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    all_reviews = []
    seen_ids = set()  # Avoid duplicates across countries
    
    print(f"Scraping reviews from Apple App Store RSS for app: {app_id}")
    print(f"Countries: {', '.join(countries)}")
    print(f"Max pages per country: {max_pages}")
    print(f"Date cutoff: {cutoff_date.isoformat()}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for country in countries:
        print(f"\nScraping from country: {country.upper()}")
        
        try:
            country_reviews = []
            
            for page in range(1, max_pages + 1):
                try:
                    # Try base URL without page first for debugging
                    if page == 1:
                        base_url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"
                        print(f"  Trying base URL: {base_url}")
                        base_response = requests.get(base_url, headers=headers, timeout=10)
                        base_data = base_response.json()
                        base_entries = base_data.get("feed", {}).get("entry", [])
                        print(f"  Base URL entries: {len(base_entries)}")
                    
                    # Correct URL format
                    url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/page={page}/json"
                    
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    print(f"  Response keys: {list(data.keys())}")
                    feed = data.get("feed", {})
                    print(f"  Feed keys: {list(feed.keys())}")
                    entries = feed.get("entry", [])
                    print(f"  Total entries: {len(entries)}")
                    
                    if not entries:
                        print(f"  Page {page}: No more reviews available")
                        break
                    
                    # Skip first entry (app metadata, not a review)
                    reviews = entries[1:] if len(entries) > 1 else []
                    
                    if not reviews:
                        print(f"  Page {page}: No reviews (only metadata)")
                        break
                    
                    page_reviews = []
                    for entry in reviews:
                        try:
                            # Extract review ID
                            review_id = entry.get("id", {}).get("label", "")
                            if not review_id or review_id in seen_ids:
                                continue
                            
                            # Extract rating
                            rating = entry.get("im:rating", {}).get("label", 0)
                            try:
                                rating = int(rating)
                            except (ValueError, TypeError):
                                rating = 0
                            
                            # Extract text
                            text = entry.get("content", {}).get("label", "")
                            
                            # Extract date
                            date_str = entry.get("updated", {}).get("label", "")
                            if not date_str:
                                continue
                            
                            try:
                                review_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            except (ValueError, TypeError):
                                continue
                            
                            # Check if review is within date window
                            if review_date < cutoff_date:
                                continue
                            
                            seen_ids.add(review_id)
                            
                            # Normalize to raw_reviews schema
                            normalized = {
                                "id": review_id,
                                "source": "app_store",
                                "rating": rating,
                                "review_date": review_date.isoformat(),
                                "text": text
                            }
                            
                            page_reviews.append(normalized)
                            
                        except Exception as e:
                            print(f"    ✗ Error parsing review: {e}")
                            continue
                    
                    country_reviews.extend(page_reviews)
                    print(f"  Page {page}: {len(page_reviews)} new reviews (total: {len(country_reviews)})")
                    
                    if len(page_reviews) == 0:
                        print(f"  No more reviews available")
                        break
                    
                    # Polite rate limiting between pages
                    time.sleep(0.5)
                    
                except requests.exceptions.RequestException as e:
                    print(f"  ✗ Error fetching page {page}: {e}")
                    break
                except Exception as e:
                    print(f"  ✗ Error parsing page {page}: {e}")
                    break
            
            all_reviews.extend(country_reviews)
            print(f"✓ Completed {country.upper()}: {len(country_reviews)} reviews within {days}-day window")
            
            # Polite rate limiting between countries
            time.sleep(1.0)
            
        except Exception as e:
            print(f"✗ Error scraping {country.upper()}: {e}")
            print(f"  Continuing to next country...")
            continue
    
    print(f"\n✓ Total unique reviews across all countries: {len(all_reviews)}")
    print(f"✓ Reviews within {days}-day window: {len(all_reviews)}")
    
    return all_reviews

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
            print(f"  ✗ Failed to upsert review {review['id']}: {e}")
    
    print(f"\n✓ Upsert complete: {success_count} successful, {failure_count} failed")
    return success_count, failure_count

def main():
    """Main execution function."""
    print("=" * 60)
    print("Phase 2b: App Store Ingestor")
    print("=" * 60)
    
    # Scrape reviews from multiple countries using RSS JSON endpoint
    raw_reviews = scrape_app_store_reviews(days=90, countries=["us", "gb", "ca", "au", "in"], max_pages=10)
    
    if not raw_reviews:
        print("\n✗ No reviews scraped. Exiting.")
        return
    
    # Upsert to Supabase
    success_count, failure_count = upsert_reviews_to_supabase(raw_reviews)
    
    print("\n" + "=" * 60)
    print(f"Phase 2b Complete")
    print(f"Total reviews processed: {len(raw_reviews)}")
    print(f"Successfully upserted: {success_count}")
    print(f"Failed: {failure_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
