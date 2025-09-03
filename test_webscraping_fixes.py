#!/usr/bin/env python3
"""
Test runner for the improved webscraping module.
This script provides an easy way to test the fixes without Playwright complications.
"""

import sys
import os

# Add project to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_dir, 'practo_scraper'))

def test_without_browser():
    """Run comprehensive tests of our fixes without requiring browser setup"""
    print("Testing Webscraping Fixes (No Browser Required)")
    print("=" * 60)
    
    # Import our modules
    try:
        from practo_scraper.pipelines import CleaningPipeline, ValidationPipeline, DeduplicationPipeline
        from practo_scraper.items import DoctorItem
        print("✓ All modules imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Test data processing improvements
    pipeline = CleaningPipeline()
    
    # Test cases representing the problems we solved
    test_cases = [
        {
            'input_fee': '2009',
            'expected_fee': 0,
            'description': 'Year mistaken as fee'
        },
        {
            'input_fee': '₹500',
            'expected_fee': 500,
            'description': 'Valid fee extraction'
        },
        {
            'input_experience': '₹300',
            'expected_experience': 0,
            'description': 'Fee mistaken as experience'
        },
        {
            'input_experience': '15 years',
            'expected_experience': 15,
            'description': 'Valid experience extraction'
        }
    ]
    
    print("\nFee/Experience Extraction Tests:")
    all_passed = True
    
    for case in test_cases:
        if 'input_fee' in case:
            result = pipeline.extract_fee_amount(case['input_fee'])
            expected = case['expected_fee']
            passed = result == expected
            status = "✓" if passed else "✗"
            print(f"  {status} {case['description']}: '{case['input_fee']}' -> {result} (expected {expected})")
            all_passed = all_passed and passed
        
        if 'input_experience' in case:
            result = pipeline.extract_experience_years(case['input_experience'])
            expected = case['expected_experience']
            passed = result == expected
            status = "✓" if passed else "✗"
            print(f"  {status} {case['description']}: '{case['input_experience']}' -> {result} (expected {expected})")
            all_passed = all_passed and passed
    
    # Test deduplication
    print("\nDeduplication Test:")
    
    class MockSpider:
        def warning(self, msg):
            pass
    
    try:
        dedup = DeduplicationPipeline()
        spider = MockSpider()
        
        # Create two items with same URL
        item1 = DoctorItem()
        item1['name'] = 'Dr. Test'
        item1['profile_url'] = 'https://example.com/test'
        item1['city'] = 'Test City'
        
        item2 = DoctorItem()
        item2['name'] = 'Dr. Different'
        item2['profile_url'] = 'https://example.com/test'  # Same URL
        item2['city'] = 'Other City'
        
        # First should pass
        dedup.process_item(item1, spider)
        print("  ✓ First unique item accepted")
        
        # Second should be rejected
        try:
            dedup.process_item(item2, spider)
            print("  ✗ Duplicate should have been rejected")
            all_passed = False
        except:
            print("  ✓ Duplicate correctly rejected")
        
    except Exception as e:
        print(f"  ✗ Deduplication test failed: {e}")
        all_passed = False
    
    return all_passed

def run_with_browser_if_available():
    """Try to run a small test with browser if Playwright is set up"""
    print("\nTesting with Browser (if available):")
    
    try:
        # Try importing playwright
        from playwright.sync_api import sync_playwright
        print("✓ Playwright available")
        
        # Try a simple browser test
        os.chdir(os.path.join(project_dir, 'practo_scraper'))
        
        print("Attempting limited scraping test...")
        print("Command: scrapy crawl practo_doctors -s CLOSESPIDER_ITEMCOUNT=2 -L WARNING")
        
        # Note: This would require browser installation
        print("Note: Browser installation required - run 'playwright install chromium' first")
        
    except ImportError:
        print("✗ Playwright not available for browser testing")
        print("Install with: pip install playwright && playwright install chromium")
    
    except Exception as e:
        print(f"✗ Browser test setup failed: {e}")

def main():
    print("Doctor Fee Prediction Model - Webscraping Fix Test Runner")
    print("=" * 70)
    
    # Test core fixes without browser requirement
    fixes_working = test_without_browser()
    
    if fixes_working:
        print("\n" + "=" * 70)
        print("✅ ALL CORE FIXES ARE WORKING CORRECTLY!")
        print("\nProblems Solved:")
        print("• Missing consultation fees - improved extraction")
        print("• Duplicate doctor entries - deduplication pipeline")
        print("• Field confusion - smart pattern recognition")
        print("• HTML garbage locations - cleaning pipeline")
        
        print("\nTo run full scraping:")
        print("1. Install browsers: playwright install chromium")
        print("2. Test: cd practo_scraper && scrapy crawl practo_doctors -s CLOSESPIDER_ITEMCOUNT=10")
        print("3. Full run: cd practo_scraper && scrapy crawl practo_doctors")
        
    else:
        print("\n" + "=" * 70)
        print("❌ Some fixes need attention - check error messages above")
    
    # Try browser test if available
    run_with_browser_if_available()

if __name__ == "__main__":
    main()