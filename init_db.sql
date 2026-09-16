-- Initialize Supabase database tables for Spotify Review Analysis Engine
-- Run this SQL in your Supabase SQL Editor (Project > SQL Editor)

-- Create raw_reviews table
CREATE TABLE IF NOT EXISTS raw_reviews (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL CHECK (source IN ('play_store', 'app_store', 'reddit', 'forum', 'social')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_date TIMESTAMPTZ NOT NULL,
    text TEXT NOT NULL,
    scraped_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create tagged_reviews table
CREATE TABLE IF NOT EXISTS tagged_reviews (
    id TEXT PRIMARY KEY REFERENCES raw_reviews(id) ON DELETE CASCADE,
    frustration_type TEXT NOT NULL CHECK (
        frustration_type IN (
            'stale_recommendations',
            'filter_bubble_lock_in',
            'discovery_friction',
            'algorithmic_sameness',
            'poor_new_release_surfacing',
            'context_blindness',
            'over_personalization',
            'control_loss',
            'none'
        )
    ),
    segment TEXT NOT NULL CHECK (
        segment IN (
            'lapsed_explorer',
            'active_explorer',
            'passive_listener',
            'genre_loyalist',
            'mood_listener',
            'podcast_first',
            'unknown'
        )
    ),
    desired_behavior TEXT NOT NULL CHECK (
        desired_behavior IN (
            'find_new_artists',
            'break_routine',
            'match_mood_or_context',
            'deep_dive_genre',
            'social_discovery',
            'rediscover_back_catalog',
            'none'
        )
    ),
    root_cause TEXT NOT NULL,
    unmet_need TEXT NOT NULL,
    discovery_related BOOLEAN NOT NULL,
    sentiment TEXT NOT NULL CHECK (sentiment IN ('positive', 'neutral', 'negative')),
    classified_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_raw_reviews_source ON raw_reviews(source);
CREATE INDEX IF NOT EXISTS idx_raw_reviews_scraped_at ON raw_reviews(scraped_at);
CREATE INDEX IF NOT EXISTS idx_tagged_reviews_discovery_related ON tagged_reviews(discovery_related);
CREATE INDEX IF NOT EXISTS idx_tagged_reviews_frustration_type ON tagged_reviews(frustration_type);
CREATE INDEX IF NOT EXISTS idx_tagged_reviews_segment ON tagged_reviews(segment);
