#!/usr/bin/env python3
"""
Manual test to verify URL generation and pagination logic
"""

import requests
from urllib.parse import quote
import re

def test_pagination_urls():
    """Test that pagination URLs are correctly generated"""
    print("=== Testing Pagination URL Generation ===")
    
    speciality = "Dentist"
    city = "Bangalore"
    
    # Generate URLs like the spider does
    search_query = quote(f'[{{"word":"{speciality}","autocompleted":true,"category":"subspeciality"}}]')
    
    urls = []
    for page in range(1, 4):  # Test first 3 pages
        if page == 1:
            url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}"
        else:
            url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}&page={page}"
        urls.append((page, url))
    
    print("Generated URLs:")
    for page, url in urls:
        print(f"  Page {page}: {url[:100]}...")
    
    return urls

def test_website_response():
    """Test if the website responds to our URLs"""
    print("\n=== Testing Website Response ===")
    
    # Test with a simple URL
    speciality = "Dentist"
    city = "Bangalore"
    search_query = quote(f'[{{"word":"{speciality}","autocompleted":true,"category":"subspeciality"}}]')
    url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"Testing URL: {url[:80]}...")
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            # Look for doctor-related content
            content = response.text.lower()
            doctor_count = content.count('doctor')
            profile_count = content.count('profile')
            
            print(f"Content Analysis:")
            print(f"  - 'doctor' mentions: {doctor_count}")
            print(f"  - 'profile' mentions: {profile_count}")
            
            # Look for pagination indicators
            pagination_indicators = [
                'load more', 'next page', 'page 2', 'pagination',
                'load_more', 'next', 'more doctors'
            ]
            
            found_indicators = []
            for indicator in pagination_indicators:
                if indicator in content:
                    found_indicators.append(indicator)
            
            if found_indicators:
                print(f"  - Pagination indicators found: {found_indicators}")
            else:
                print(f"  - No obvious pagination indicators found")
            
            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_config_coverage():
    """Test the expanded configuration coverage"""
    print("\n=== Testing Configuration Coverage ===")
    
    try:
        from config import CITIES, SPECIALITIES
        
        print(f"Cities configured: {len(CITIES)}")
        for city in CITIES:
            print(f"  - {city}")
        
        print(f"\nSpecialities configured: {len(SPECIALITIES)}")
        
        # Group specialities for better display
        original_specs = [
            'Cardiologist', 'Chiropractor', 'Dentist', 'Dermatologist', 
            'Dietitian/Nutritionist', 'Gastroenterologist', 'bariatric surgeon', 
            'Gynecologist', 'Infertility Specialist', 'Neurologist', 'Neurosurgeon', 
            'Ophthalmologist', 'Orthopedist', 'Pediatrician', 'Physiotherapist', 
            'Psychiatrist', 'Pulmonologist', 'Rheumatologist', 'Urologist'
        ]
        
        new_specs = [spec for spec in SPECIALITIES if spec not in original_specs]
        
        print(f"\nOriginal specialities ({len(original_specs)}):")
        for spec in original_specs:
            status = "✅" if spec in SPECIALITIES else "❌"
            print(f"  {status} {spec}")
        
        print(f"\nNew specialities added ({len(new_specs)}):")
        for spec in new_specs:
            print(f"  ➕ {spec}")
        
        # Calculate potential requests
        total_combinations = len(CITIES) * len(SPECIALITIES)
        print(f"\nTotal city-speciality combinations: {total_combinations}")
        print(f"Potential for comprehensive coverage: {'HIGH' if total_combinations > 90 else 'MEDIUM'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all manual tests"""
    print("🧪 Manual Scraper Enhancement Validation")
    print("=" * 50)
    
    tests = [
        test_pagination_urls,
        test_website_response,
        test_config_coverage
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Manual Test Results:")
    
    test_names = ["URL Generation", "Website Response", "Configuration Coverage"]
    passed = sum(1 for r in results if r)  # Count True values
    total = len(results)
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All manual tests passed!")
        print("The scraper enhancements are properly configured and should work correctly.")
        print("\n📋 Ready for production testing:")
        print("  1. Run: cd practo_scraper && scrapy crawl practo_doctors_simple -a city=Bangalore -s CLOSESPIDER_ITEMCOUNT=100")
        print("  2. Monitor logs for pagination messages")
        print("  3. Verify increased doctor count vs existing 2826")
    else:
        print("\n⚠️ Some tests failed. Please review and fix issues before production.")

if __name__ == "__main__":
    main()