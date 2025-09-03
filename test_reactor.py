#!/usr/bin/env python3
"""
Test script to check if asyncio reactor can be installed properly
"""

def test_reactor():
    """Test if we can install the asyncio reactor"""
    try:
        # Install asyncio reactor before any other Twisted imports
        import twisted.internet.asyncioreactor
        twisted.internet.asyncioreactor.install()
        print("✅ AsyncIO reactor installed successfully")
        
        # Now test if we can import scrapy-playwright
        from scrapy_playwright.handler import ScrapyPlaywrightDownloadHandler
        print("✅ scrapy-playwright import successful")
        
        # Test basic scrapy import
        import scrapy
        print("✅ Scrapy import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing reactor installation...")
    test_reactor()
