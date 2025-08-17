#!/usr/bin/env python3
"""
Test the improved Selenium-based scraper to validate selector fixes
"""
import sys
import os
sys.path.append('/home/runner/work/Doctor-Fee-Prediction-Model/Doctor-Fee-Prediction-Model')

from improved_web_scraper import ImprovedPractoScraper
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_improved_scraper():
    """Test the improved scraper with a small sample"""
    
    print("Testing improved Selenium-based scraper...")
    print("This will test the enhanced selector logic for problematic fields.")
    
    try:
        # Initialize scraper
        scraper = ImprovedPractoScraper()
        
        # Limit to just 1 city and 1 speciality for testing
        scraper.cities = ['Bangalore']
        scraper.specialities = ['Dentist']
        
        print(f"Testing with cities: {scraper.cities}")
        print(f"Testing with specialities: {scraper.specialities}")
        
        # Run scraping with very limited scope (just 3 doctors)
        print("\\nStarting test scrape...")
        scraper.scrape_all_data(max_doctors_per_speciality=3)
        
        print(f"\\nScraping completed. Total doctors scraped: {len(scraper.data)}")
        
        # Analyze the results
        if scraper.data:
            print("\\n" + "="*60)
            print("ANALYZING SCRAPED DATA")
            print("="*60)
            
            for i, doctor in enumerate(scraper.data, 1):
                print(f"\\nDoctor {i}:")
                for field, value in doctor.items():
                    status = "✅" if value and str(value).strip() else "❌"
                    print(f"  {status} {field}: {repr(value)}")
            
            # Summary of field extraction success
            print("\\n" + "="*60)
            print("FIELD EXTRACTION SUMMARY")
            print("="*60)
            
            total_doctors = len(scraper.data)
            field_stats = {}
            
            for field in scraper.data[0].keys():
                success_count = 0
                for doctor in scraper.data:
                    if doctor.get(field) and str(doctor.get(field)).strip() and str(doctor.get(field)) != "0":
                        success_count += 1
                
                success_rate = (success_count / total_doctors) * 100
                field_stats[field] = {
                    'success_count': success_count,
                    'total': total_doctors,
                    'success_rate': success_rate
                }
                
                status_emoji = "✅" if success_rate >= 50 else ("⚠️" if success_rate > 0 else "❌")
                print(f"{status_emoji} {field}: {success_count}/{total_doctors} ({success_rate:.1f}%)")
            
            # Check improvements for problematic fields
            print("\\n" + "="*60)
            print("IMPROVEMENTS CHECK")
            print("="*60)
            
            problematic_fields = ['Year_of_experience', 'npv', 'google_map_link', 'Location']
            for field in problematic_fields:
                if field in field_stats:
                    rate = field_stats[field]['success_rate']
                    if rate > 0:
                        print(f"🎯 {field}: IMPROVED! Now extracting {rate:.1f}% successfully")
                    else:
                        print(f"❌ {field}: Still not extracting data")
                else:
                    print(f"❓ {field}: Field not found in data")
            
            # Save test results
            test_filename = 'test_improved_results.csv'
            filename = scraper.save_to_csv(test_filename)
            print(f"\\n📄 Test results saved to: {filename}")
            
        else:
            print("❌ No data was scraped. Check the logs for errors.")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_scraper()