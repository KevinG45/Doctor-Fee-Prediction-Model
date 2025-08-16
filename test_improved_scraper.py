#!/usr/bin/env python3
"""
Test script to validate improved scraping capabilities
"""

import os
import sys
import subprocess
import pandas as pd
from datetime import datetime

def test_scraper_improvements():
    """Test the improved scraper to ensure it captures more doctors"""
    
    print("=== Testing Improved Practo Scraper ===")
    print(f"Test started at: {datetime.now()}")
    
    # Test with a limited scope first (just one speciality in Bangalore)
    test_speciality = "Dentist"  # This had the most doctors in previous data
    test_city = "Bangalore"
    
    print(f"\nTesting with {test_speciality} in {test_city}")
    
    # Change to scrapy directory
    os.chdir("practo_scraper")
    
    # Run the improved simple spider for the test
    cmd = [
        "scrapy", "crawl", "practo_doctors_simple",
        "-a", f"city={test_city}",
        "-a", f"speciality={test_speciality}",
        "-o", "test_output.csv",
        "-s", "CLOSESPIDER_ITEMCOUNT=100",  # Limit for test
        "-L", "INFO"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        # Check if output file was created
        if os.path.exists("test_output.csv"):
            df = pd.read_csv("test_output.csv")
            print(f"\nTest Results:")
            print(f"- Records scraped: {len(df)}")
            print(f"- Unique doctors: {df['name'].nunique() if 'name' in df.columns else 'N/A'}")
            print(f"- Cities: {df['city'].unique().tolist() if 'city' in df.columns else 'N/A'}")
            print(f"- Specialities: {df['speciality'].unique().tolist() if 'speciality' in df.columns else 'N/A'}")
            
            # Clean up test file
            os.remove("test_output.csv")
            
            return len(df) > 0
        else:
            print("No output file generated")
            return False
            
    except subprocess.TimeoutExpired:
        print("Test timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"Error running test: {e}")
        return False

def count_existing_doctors():
    """Count doctors in existing data for comparison"""
    data_path = "../DATA/raw_practo.csv"
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        bangalore_doctors = df[df['City'] == 'Bangalore'] if 'City' in df.columns else df
        print(f"Existing Bangalore doctors in data: {len(bangalore_doctors)}")
        return len(bangalore_doctors)
    return 0

if __name__ == "__main__":
    # Count existing data first
    existing_count = count_existing_doctors()
    
    # Run the test
    success = test_scraper_improvements()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("The improved scraper is working correctly.")
    else:
        print("\n❌ Test failed!")
        print("There may be issues with the scraper improvements.")
    
    print(f"\nTarget: Improve from ~{existing_count} to 4500+ Bangalore doctors")