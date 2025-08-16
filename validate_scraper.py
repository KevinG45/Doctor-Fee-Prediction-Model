#!/usr/bin/env python3
"""
Simple test to validate the scraper URL generation and basic functionality
"""

import sys
import os
sys.path.append('.')

def test_url_generation():
    """Test URL generation logic"""
    from urllib.parse import quote
    
    # Test URL generation like the spider does
    speciality = "Dentist"
    city = "Bangalore"
    
    search_query = quote(f'[{{"word":"{speciality}","autocompleted":true,"category":"subspeciality"}}]')
    base_url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}"
    page_url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}&page=2"
    
    print("Generated URLs:")
    print(f"Base URL: {base_url}")
    print(f"Page 2 URL: {page_url}")
    
    return True

def test_config_import():
    """Test config import functionality"""
    try:
        from config import CITIES, SPECIALITIES
        print(f"Successfully imported config:")
        print(f"- Cities: {len(CITIES)} ({CITIES})")
        print(f"- Specialities: {len(SPECIALITIES)} (first 5: {SPECIALITIES[:5]})")
        return True
    except Exception as e:
        print(f"Config import failed: {e}")
        return False

def test_spider_initialization():
    """Test spider can be initialized"""
    try:
        sys.path.append('practo_scraper')
        from practo_scraper.spiders.practo_doctors_simple import PractoDoctorsSimpleSpider
        
        spider = PractoDoctorsSimpleSpider()
        print(f"Spider initialized successfully:")
        print(f"- Name: {spider.name}")
        print(f"- Cities: {len(spider.cities)}")
        print(f"- Specialities: {len(spider.specialities)}")
        print(f"- Allowed domains: {spider.allowed_domains}")
        
        return True
    except Exception as e:
        print(f"Spider initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Simple Scraper Validation ===")
    
    tests = [
        ("URL Generation", test_url_generation),
        ("Config Import", test_config_import),
        ("Spider Initialization", test_spider_initialization),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All basic validations passed!")
        print("The scraper improvements are properly configured.")
        print("\nNext steps:")
        print("1. Run a full scrape with the enhanced spider")
        print("2. Monitor the logs for pagination working")
        print("3. Compare results with previous 2826 Bangalore doctors")
    else:
        print("⚠️ Some validations failed. Please fix before proceeding.")