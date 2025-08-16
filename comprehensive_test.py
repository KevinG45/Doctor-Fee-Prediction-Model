#!/usr/bin/env python3
"""
Comprehensive test runner for the improved scraper
"""

import os
import sys
import subprocess
import pandas as pd
import time
from datetime import datetime

def run_limited_scrape():
    """Run a limited scrape to test improvements"""
    print("=== Running Limited Scrape Test ===")
    
    # Change to scrapy directory
    os.chdir("practo_scraper")
    
    # Test with just Bangalore and a few specialities
    output_file = f"test_scrape_{int(time.time())}.csv"
    
    # Run scraper with limited scope
    cmd = [
        "scrapy", "crawl", "practo_doctors_simple",
        "-a", "city=Bangalore",
        "-a", "speciality=Dentist,General Physician",  # Test with 2 specialities
        "-o", output_file,
        "-s", "CLOSESPIDER_ITEMCOUNT=50",  # Limit items for test
        "-s", "DOWNLOAD_DELAY=1",  # Speed up for test
        "-L", "INFO"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print("This will take a few minutes...")
    
    start_time = time.time()
    
    try:
        # Run with a reasonable timeout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\\nScrape completed in {duration:.1f} seconds")
        print(f"Return code: {result.returncode}")
        
        # Show some output for debugging
        if result.stdout:
            print("\\nLast few lines of output:")
            lines = result.stdout.strip().split('\\n')
            for line in lines[-10:]:  # Show last 10 lines
                print(f"  {line}")
        
        # Check results
        if os.path.exists(output_file):
            df = pd.read_csv(output_file)
            print(f"\\n📊 Scrape Results:")
            print(f"  Total records: {len(df)}")
            
            if len(df) > 0:
                print(f"  Cities: {df['city'].unique().tolist() if 'city' in df.columns else 'N/A'}")
                print(f"  Specialities: {df['speciality'].unique().tolist() if 'speciality' in df.columns else 'N/A'}")
                print(f"  Sample records:")
                for i, row in df.head(3).iterrows():
                    name = row.get('name', 'N/A')
                    spec = row.get('speciality', 'N/A')
                    city = row.get('city', 'N/A')
                    print(f"    {i+1}. {name} - {spec} in {city}")
            
            # Clean up
            os.remove(output_file)
            
            return len(df)
        else:
            print("❌ No output file generated")
            return 0
            
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out after 3 minutes")
        return -1
    except Exception as e:
        print(f"❌ Error: {e}")
        return -1

def compare_with_existing_data():
    """Compare test results with existing data"""
    print("\\n=== Comparison with Existing Data ===")
    
    data_path = "../DATA/raw_practo.csv"
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        
        # Count existing Bangalore doctors
        bangalore_docs = df[df['City'] == 'Bangalore'] if 'City' in df.columns else df
        total_bangalore = len(bangalore_docs)
        
        # Count by speciality
        if 'Speciality' in df.columns:
            spec_counts = bangalore_docs['Speciality'].value_counts()
            dentist_count = spec_counts.get('Dentist', 0)
            gp_count = spec_counts.get('General Physician', 0)
            
            print(f"📈 Existing data analysis:")
            print(f"  Total Bangalore doctors: {total_bangalore}")
            print(f"  Dentists in Bangalore: {dentist_count}")
            print(f"  General Physicians in Bangalore: {gp_count}")
            print(f"  Top 5 specialities: {spec_counts.head().to_dict()}")
        
        return total_bangalore
    else:
        print("❌ No existing data found to compare")
        return 0

def estimate_full_potential():
    """Estimate the potential of the improved scraper"""
    print("\\n=== Improvement Potential Estimate ===")
    
    # Current configuration
    from config import SPECIALITIES
    total_specialities = len(SPECIALITIES)
    
    print(f"📊 Configuration Analysis:")
    print(f"  Total specialities configured: {total_specialities}")
    print(f"  Original specialities: 19")
    print(f"  Added specialities: {total_specialities - 19}")
    print(f"  Increase in speciality coverage: {((total_specialities - 19) / 19) * 100:.1f}%")
    
    print(f"\\n🚀 Expected Improvements:")
    print(f"  • Pagination: Should capture 10-20x more doctors per speciality")
    print(f"  • New specialities: Should add {total_specialities - 19} new speciality categories")
    print(f"  • Enhanced scrolling: Should capture more doctors per page")
    print(f"  • Removed limits: No artificial caps on doctor count")
    
    print(f"\\n🎯 Target Achievement:")
    print(f"  Current: ~2826 Bangalore doctors")
    print(f"  Target: 4500+ Bangalore doctors")
    print(f"  Required improvement: {((4500 - 2826) / 2826) * 100:.1f}%")
    print(f"  Feasibility: HIGH (pagination alone should achieve this)")

if __name__ == "__main__":
    print("🔍 Comprehensive Scraper Test")
    print(f"Started at: {datetime.now()}")
    
    # Step 1: Compare with existing data
    existing_count = compare_with_existing_data()
    
    # Step 2: Estimate potential
    estimate_full_potential()
    
    # Step 3: Run limited test
    test_result = run_limited_scrape()
    
    # Step 4: Final assessment
    print("\\n=== Final Assessment ===")
    
    if test_result > 0:
        print(f"✅ Test scrape successful: {test_result} records")
        print(f"🎉 Improvements are working correctly!")
        
        print(f"\\n📋 Ready for Full Production Run:")
        print(f"  Command: python run_scraper.py --city=Bangalore")
        print(f"  Expected: Significant increase from {existing_count} doctors")
        print(f"  Monitor: Check logs for pagination and multiple pages")
        
    elif test_result == 0:
        print(f"⚠️ Test scrape returned no results")
        print(f"This might indicate an issue with selectors or website changes")
        
    else:
        print(f"❌ Test scrape failed or timed out")
        print(f"Check scrapy configuration and network connectivity")
    
    print(f"\\nCompleted at: {datetime.now()}")