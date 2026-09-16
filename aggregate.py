"""
Phase 4: Aggregation
Queries tagged_reviews joined to raw_reviews and generates insights.
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from collections import Counter, defaultdict

# Load environment variables
load_dotenv()

def get_all_classified_reviews():
    """
    Fetch all classified reviews from tagged_reviews joined with raw_reviews.
    
    Returns:
        List of dictionaries with combined review data
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Get all tagged reviews joined with raw reviews
    response = supabase.table("tagged_reviews").select(
        "*, raw_reviews(source, rating, review_date, text)"
    ).execute()
    
    return response.data

def calculate_insights(reviews):
    """
    Calculate insights from classified reviews.
    
    Args:
        reviews: List of classified review dictionaries
    
    Returns:
        Dictionary with all insights
    """
    total_reviews = len(reviews)
    discovery_related = [r for r in reviews if r.get('discovery_related') == True]
    discovery_count = len(discovery_related)
    discovery_percent = (discovery_count / total_reviews * 100) if total_reviews > 0 else 0
    
    # Counts by category
    frustration_counts = Counter(r.get('frustration_type') for r in discovery_related)
    segment_counts = Counter(r.get('segment') for r in discovery_related)
    behavior_counts = Counter(r.get('desired_behavior') for r in discovery_related)
    source_counts = Counter(r.get('raw_reviews', {}).get('source') for r in discovery_related)
    
    # Segment × Frustration crosstab
    crosstab = defaultdict(lambda: defaultdict(int))
    for r in discovery_related:
        segment = r.get('segment') or 'unknown'
        frustration = r.get('frustration_type') or 'none'
        crosstab[segment][frustration] += 1
    
    # Top root_cause and unmet_need phrases
    root_causes = Counter(r.get('root_cause') for r in discovery_related if r.get('root_cause'))
    unmet_needs = Counter(r.get('unmet_need') for r in discovery_related if r.get('unmet_need'))
    
    insights = {
        'total_reviews': total_reviews,
        'discovery_related': {
            'count': discovery_count,
            'percent': round(discovery_percent, 1)
        },
        'by_frustration_type': dict(frustration_counts.most_common()),
        'by_segment': dict(segment_counts.most_common()),
        'by_desired_behavior': dict(behavior_counts.most_common()),
        'by_source': dict(source_counts.most_common()),
        'segment_x_frustration_crosstab': {seg: dict(frus) for seg, frus in crosstab.items()},
        'top_root_causes': dict(root_causes.most_common(10)),
        'top_unmet_needs': dict(unmet_needs.most_common(10))
    }
    
    return insights

def save_insights_json(insights, filepath='insights.json'):
    """Save insights to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(insights, f, indent=2)
    print(f"✓ Saved insights to {filepath}")

def save_insights_markdown(insights, filepath='insights.md'):
    """Save insights to Markdown file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("# Spotify Discovery Review Analysis - Insights\n\n")
        
        f.write("## Overview\n\n")
        f.write(f"- **Total classified reviews**: {insights['total_reviews']}\n")
        f.write(f"- **Discovery-related**: {insights['discovery_related']['count']} ({insights['discovery_related']['percent']}%)\n\n")
        
        f.write("## By Frustration Type\n\n")
        f.write("| Frustration Type | Count |\n")
        f.write("|------------------|-------|\n")
        for ft, count in insights['by_frustration_type'].items():
            f.write(f"| {ft} | {count} |\n")
        f.write("\n")
        
        f.write("## By Segment\n\n")
        f.write("| Segment | Count |\n")
        f.write("|---------|-------|\n")
        for seg, count in insights['by_segment'].items():
            f.write(f"| {seg} | {count} |\n")
        f.write("\n")
        
        f.write("## By Desired Behavior\n\n")
        f.write("| Desired Behavior | Count |\n")
        f.write("|------------------|-------|\n")
        for db, count in insights['by_desired_behavior'].items():
            f.write(f"| {db} | {count} |\n")
        f.write("\n")
        
        f.write("## By Source\n\n")
        f.write("| Source | Count |\n")
        f.write("|--------|-------|\n")
        for src, count in insights['by_source'].items():
            f.write(f"| {src} | {count} |\n")
        f.write("\n")
        
        f.write("## Segment × Frustration Type Crosstab\n\n")
        f.write("| Segment | Frustration Type | Count |\n")
        f.write("|---------|------------------|-------|\n")
        for segment, frustrations in insights['segment_x_frustration_crosstab'].items():
            for frustration, count in frustrations.items():
                f.write(f"| {segment} | {frustration} | {count} |\n")
        f.write("\n")
        
        f.write("## Top Root Causes\n\n")
        f.write("| Rank | Root Cause | Count |\n")
        f.write("|------|------------|-------|\n")
        for rank, (cause, count) in enumerate(insights['top_root_causes'].items(), 1):
            f.write(f"| {rank} | {cause} | {count} |\n")
        f.write("\n")
        
        f.write("## Top Unmet Needs\n\n")
        f.write("| Rank | Unmet Need | Count |\n")
        f.write("|------|------------|-------|\n")
        for rank, (need, count) in enumerate(insights['top_unmet_needs'].items(), 1):
            f.write(f"| {rank} | {need} | {count} |\n")
        f.write("\n")
    
    print(f"✓ Saved insights to {filepath}")

def print_summary(insights):
    """Print summary to console."""
    print("\n" + "=" * 60)
    print("Phase 4: Aggregation - Summary")
    print("=" * 60)
    print(f"\nTotal classified reviews: {insights['total_reviews']}")
    print(f"Discovery-related: {insights['discovery_related']['count']} ({insights['discovery_related']['percent']}%)")
    
    print(f"\n--- Top Frustration Types ---")
    for ft, count in list(insights['by_frustration_type'].items())[:5]:
        print(f"  {ft}: {count}")
    
    print(f"\n--- Top Segments ---")
    for seg, count in list(insights['by_segment'].items())[:5]:
        print(f"  {seg}: {count}")
    
    print(f"\n--- Top Desired Behaviors ---")
    for db, count in list(insights['by_desired_behavior'].items())[:5]:
        print(f"  {db}: {count}")
    
    print(f"\n--- Top Root Causes ---")
    for rank, (cause, count) in enumerate(list(insights['top_root_causes'].items())[:5], 1):
        print(f"  {rank}. {cause}: {count}")
    
    print(f"\n--- Top Unmet Needs ---")
    for rank, (need, count) in enumerate(list(insights['top_unmet_needs'].items())[:5], 1):
        print(f"  {rank}. {need}: {count}")
    
    print("\n" + "=" * 60)

def main():
    """Main execution function."""
    print("=" * 60)
    print("Phase 4: Aggregation")
    print("=" * 60)
    
    print("\nFetching classified reviews...")
    reviews = get_all_classified_reviews()
    
    if not reviews:
        print("✗ No classified reviews found")
        return
    
    print(f"✓ Fetched {len(reviews)} classified reviews")
    
    print("\nCalculating insights...")
    insights = calculate_insights(reviews)
    
    print("\nSaving insights...")
    save_insights_json(insights)
    save_insights_markdown(insights)
    
    print_summary(insights)
    print("\n✓ Aggregation complete")

if __name__ == "__main__":
    main()
