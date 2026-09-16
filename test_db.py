"""
Phase 1: Database Connection Test
Tests Supabase connection by inserting a dummy row and reading it back.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test Supabase connection with insert and read operations."""
    
    # Get environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    
    print(f"Connecting to Supabase at: {supabase_url}")
    
    # Initialize Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Test data
    test_id = "test_001"
    test_data = {
        "id": test_id,
        "source": "play_store",
        "rating": 5,
        "review_date": datetime.now().isoformat(),
        "text": "This is a test review for Phase 1 connectivity check."
    }
    
    print(f"\nInserting test row with id: {test_id}")
    
    # Insert test row
    try:
        result = supabase.table("raw_reviews").insert(test_data).execute()
        print("✓ Insert successful")
    except Exception as e:
        print(f"✗ Insert failed: {e}")
        print("\nNOTE: Make sure you've created the 'raw_reviews' table in Supabase first.")
        print("Run the SQL in init_db.sql in your Supabase SQL editor.")
        return False
    
    # Read back the test row
    print(f"\nReading back test row with id: {test_id}")
    try:
        result = supabase.table("raw_reviews").select("*").eq("id", test_id).execute()
        rows = result.data
        
        if not rows:
            print("✗ Read failed: No rows returned")
            return False
        
        print("✓ Read successful")
        print(f"\nRetrieved row:")
        for key, value in rows[0].items():
            print(f"  {key}: {value}")
        
        # Clean up - delete the test row
        print(f"\nCleaning up test row...")
        supabase.table("raw_reviews").delete().eq("id", test_id).execute()
        print("✓ Cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Read failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1: Supabase Connection Test")
    print("=" * 60)
    
    success = test_supabase_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed! Database connection is working.")
    else:
        print("✗ Tests failed. Please check the errors above.")
    print("=" * 60)
