"""
Optional Reddit Ingestor
Fetches posts from Reddit's public .json endpoints (no API credentials required).
"""

import os
import hashlib
import time
import requests
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
        source: Source identifier (e.g., 'reddit')
        text: Review text content
    
    Returns:
        String ID (hex digest of SHA256 hash)
    """
    combined = f"{source}:{text}"
    return hashlib.sha256(combined.encode()).hexdigest()

def fetch_reddit_posts(subreddit, query, limit=100):
    """
    Fetch posts from Reddit's public .json endpoint.
    
    Args:
        subreddit: Subreddit name (e.g., 'spotify')
        query: Search query
        limit: Number of posts to fetch (default: 100)
    
    Returns:
        List of post dictionaries
    """
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        'q': query,
        'restrict_sr': '1',
        'limit': limit,
        'sort': 'relevance'
    }
    headers = {
        'User-Agent': 'SpotifyDiscovery/1.0 (research project; contact: project-research@example.com)'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        posts = data.get('data', {}).get('children', [])
        
        return [post['data'] for post in posts]
        
    except Exception as e:
        print(f"  ✗ Error fetching from r/{subreddit} with query '{query}': {e}")
        return []

def normalize_reddit_post(post):
    """
    Normalize a Reddit post to raw_reviews schema.
    
    Args:
        post: Reddit post dictionary
    
    Returns:
        Dictionary matching raw_reviews schema
    """
    # Extract title and selftext
    title = post.get('title', '')
    selftext = post.get('selftext', '')
    
    # Combine title and selftext
    text = f"{title}. {selftext}".strip()
    
    # Generate stable ID
    review_id = generate_stable_id('reddit', text)
    
    return {
        "id": review_id,
        "source": "reddit",
        "rating": None,  # Reddit doesn't have ratings
        "review_date": datetime.now().isoformat(),  # Use current time
        "text": text
    }

def upsert_reviews_to_supabase(reviews):
    """
    Upsert reviews to Supabase raw_reviews table.
    Uses generated ID as primary key to prevent duplicates.
    
    Args:
        reviews: List of dictionaries matching raw_reviews schema
    
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
    
    for review in reviews:
        try:
            supabase.table("raw_reviews").upsert(review, on_conflict="id").execute()
            success_count += 1
            
        except Exception as e:
            failure_count += 1
            print(f"  ✗ Failed to upsert review: {e}")
    
    print(f"\n✓ Upsert complete: {success_count} successful, {failure_count} failed")
    return success_count, failure_count

def main():
    """Main execution function."""
    print("=" * 60)
    print("Optional Reddit Ingestor")
    print("=" * 60)
    
    # Subreddits and queries to search
    searches = [
        ('spotify', 'discover weekly'),
        ('spotify', 'recommendations'),
        ('spotify', 'same songs'),
        ('spotify', 'discovery'),
        ('truespotify', 'discover weekly'),
        ('truespotify', 'recommendations'),
        ('truespotify', 'same songs'),
        ('truespotify', 'discovery'),
    ]
    
    all_posts = []
    seen_ids = set()
    
    print("\nFetching posts from Reddit...")
    
    try:
        for subreddit, query in searches:
            print(f"\nSearching r/{subreddit} for '{query}'...")
            
            posts = fetch_reddit_posts(subreddit, query, limit=100)
            
            if not posts:
                print(f"  No posts found")
                continue
            
            print(f"  Found {len(posts)} posts")
            
            for post in posts:
                normalized = normalize_reddit_post(post)
                
                # Skip duplicates
                if normalized['id'] in seen_ids:
                    continue
                
                seen_ids.add(normalized['id'])
                all_posts.append(normalized)
            
            # Polite rate limiting
            time.sleep(1.0)
        
        if not all_posts:
            print("\n✗ No posts fetched from Reddit")
            print("  Reddit may have blocked the public API or no results were found.")
            print("  You may need to hand-collect Reddit posts instead.")
            return
        
        print(f"\n✓ Total unique posts fetched: {len(all_posts)}")
        
        # Upsert to Supabase
        success_count, failure_count = upsert_reviews_to_supabase(all_posts)
        
        print("\n" + "=" * 60)
        print(f"Reddit Ingestor Complete")
        print(f"Total posts processed: {len(all_posts)}")
        print(f"Successfully upserted: {success_count}")
        print(f"Failed: {failure_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during Reddit ingestion: {e}")
        print("  This is optional - you can hand-collect Reddit posts instead.")

if __name__ == "__main__":
    main()
