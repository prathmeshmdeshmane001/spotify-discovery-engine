"""
Phase 2c: Paste Importer
Reads manually collected reviews from paste_sources.txt and upserts to Supabase.
"""

import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def generate_stable_id(source, text):
    """
    Generate a stable ID for a review based on source and text.
    Uses SHA256 hash of source + text.
    
    Args:
        source: Source identifier (e.g., 'forum', 'social', 'reddit', 'app_store')
        text: Review text content
    
    Returns:
        String ID (hex digest of SHA256 hash)
    """
    combined = f"{source}:{text}"
    return hashlib.sha256(combined.encode()).hexdigest()

def parse_paste_sources(filepath):
    """
    Parse paste_sources.txt file.
    Format: rating | source | text
    Lines starting with # are comments.
    
    Args:
        filepath: Path to paste_sources.txt
    
    Returns:
        List of dictionaries with keys: rating, source, text
    """
    reviews = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse format: rating | source | text
            parts = line.split('|', 2)
            
            if len(parts) < 3:
                print(f"  ✗ Line {line_num}: Invalid format (expected 'rating | source | text')")
                continue
            
            rating_part = parts[0].strip()
            source = parts[1].strip()
            text = parts[2].strip()
            
            # Parse rating (may be blank for forum/social)
            if rating_part:
                try:
                    rating = int(rating_part)
                    if not 1 <= rating <= 5:
                        print(f"  ✗ Line {line_num}: Invalid rating '{rating_part}' (must be 1-5)")
                        continue
                except ValueError:
                    print(f"  ✗ Line {line_num}: Invalid rating '{rating_part}' (must be integer 1-5)")
                    continue
            else:
                rating = None
            
            # Validate source
            valid_sources = ['forum', 'social', 'reddit', 'app_store']
            if source not in valid_sources:
                print(f"  ✗ Line {line_num}: Invalid source '{source}' (must be one of: {', '.join(valid_sources)})")
                continue
            
            reviews.append({
                'rating': rating,
                'source': source,
                'text': text
            })
    
    return reviews

def upsert_reviews_to_supabase(reviews):
    """
    Upsert reviews to Supabase raw_reviews table.
    Uses generated ID as primary key to prevent duplicates.
    
    Args:
        reviews: List of dictionaries with keys: rating, source, text
    
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
    
    current_time = datetime.now().isoformat()
    
    for review in reviews:
        try:
            # Generate stable ID
            review_id = generate_stable_id(review['source'], review['text'])
            
            # Normalize to raw_reviews schema
            normalized = {
                "id": review_id,
                "source": review['source'],
                "rating": review['rating'],
                "review_date": current_time,  # Use current time since paste doesn't have dates
                "text": review['text']
            }
            
            # Upsert using review ID as primary key
            supabase.table("raw_reviews").upsert(normalized, on_conflict="id").execute()
            success_count += 1
            
        except Exception as e:
            failure_count += 1
            print(f"  ✗ Failed to upsert review: {e}")
    
    print(f"\n✓ Upsert complete: {success_count} successful, {failure_count} failed")
    return success_count, failure_count

def main():
    """Main execution function."""
    print("=" * 60)
    print("Phase 2c: Paste Importer")
    print("=" * 60)
    
    filepath = "paste_sources.txt"
    
    if not os.path.exists(filepath):
        print(f"\n✗ File not found: {filepath}")
        return
    
    print(f"\nReading from: {filepath}")
    
    # Parse paste sources
    reviews = parse_paste_sources(filepath)
    
    if not reviews:
        print("\n✗ No valid reviews found in file.")
        return
    
    print(f"\n✓ Parsed {len(reviews)} valid reviews")
    
    # Count by source
    source_counts = {}
    for review in reviews:
        source = review['source']
        source_counts[source] = source_counts.get(source, 0) + 1
    
    print("\nReviews by source:")
    for source, count in sorted(source_counts.items()):
        print(f"  {source}: {count}")
    
    # Upsert to Supabase
    success_count, failure_count = upsert_reviews_to_supabase(reviews)
    
    print("\n" + "=" * 60)
    print(f"Phase 2c Complete")
    print(f"Total reviews processed: {len(reviews)}")
    print(f"Successfully upserted: {success_count}")
    print(f"Failed: {failure_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
