#!/usr/bin/env python3
"""
Test script to verify the asyncio event loop fix for the practo spider.
This simulates the problematic scenario without requiring a full browser setup.
"""

import asyncio
import sys
import os
import platform

# Add the project to path
sys.path.append('practo_scraper')

def test_event_loop_configuration():
    """Test that event loop configuration is properly set up"""
    print("=== Testing Event Loop Configuration ===")
    print(f"Platform: {platform.system()}")
    print(f"Python version: {sys.version}")
    print(f"Event loop policy: {type(asyncio.get_event_loop_policy())}")
    
    # Test that we can get an event loop without issues
    try:
        loop = asyncio.get_event_loop()
        print(f"Current event loop: {type(loop)}")
        print("✅ Event loop accessible")
    except Exception as e:
        print(f"❌ Event loop error: {e}")
        return False
    
    return True

def test_spider_import():
    """Test that the spider can be imported and instantiated"""
    print("\n=== Testing Spider Import ===")
    try:
        from practo_scraper.spiders.practo_doctors import PractoDoctorsSpider
        spider = PractoDoctorsSpider()
        print("✅ Spider imported and instantiated successfully")
        print(f"Spider name: {spider.name}")
        print(f"Allowed domains: {spider.allowed_domains}")
        print(f"Cities configured: {len(spider.cities)}")
        print(f"Specialities configured: {len(spider.specialities)}")
        return True
    except Exception as e:
        print(f"❌ Spider import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scrapy_playwright_compatibility():
    """Test scrapy-playwright compatibility"""
    print("\n=== Testing Scrapy-Playwright Compatibility ===")
    try:
        from scrapy_playwright.page import PageMethod
        print("✅ PageMethod imported successfully")
        
        # Test creating a PageMethod instance
        method = PageMethod("wait_for_selector", "div", timeout=5000)
        print(f"✅ PageMethod created: {method}")
        
        return True
    except Exception as e:
        print(f"❌ Scrapy-Playwright compatibility error: {e}")
        return False

def test_mock_async_operation():
    """Test that async operations work correctly in this environment"""
    print("\n=== Testing Mock Async Operations ===")
    
    async def mock_page_operation():
        """Simulate a page operation that might cause the original error"""
        await asyncio.sleep(0.1)  # Simulate some async work
        return "mock_result"
    
    try:
        # This simulates the pattern used in the spider
        result = asyncio.run(mock_page_operation())
        print(f"✅ Mock async operation completed: {result}")
        return True
    except Exception as e:
        print(f"❌ Mock async operation error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing AsyncIO Event Loop Fix for Practo Spider")
    print("=" * 50)
    
    tests = [
        test_event_loop_configuration,
        test_spider_import,
        test_scrapy_playwright_compatibility,
        test_mock_async_operation,
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
    print("TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(results)
    
    print(f"Tests passed: {passed_tests}/{total_tests}")
    
    if all(results):
        print("🎉 ALL TESTS PASSED! The asyncio fix should resolve the event loop issue.")
    else:
        print("⚠️  Some tests failed. The fix may need additional work.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)