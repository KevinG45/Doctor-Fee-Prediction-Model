#!/usr/bin/env python3
"""
Test script for the improved web scraping implementation
"""

import os
import sys
import logging

# Add the project directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'practo_scraper'))

def test_imports():
    """Test that all imports work correctly"""
    try:
        from practo_scraper.items import DoctorItem
        from practo_scraper.pipelines import ValidationPipeline, CleaningPipeline, CsvExportPipeline
        from practo_scraper.spiders.practo_doctors_simple import PractoDoctorsSimpleSpider
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_item_creation():
    """Test item creation and field access"""
    try:
        from practo_scraper.items import DoctorItem
        
        item = DoctorItem()
        item['name'] = "Dr. Test Doctor"
        item['speciality'] = "Cardiologist"
        item['consultation_fee'] = "500"
        
        assert item['name'] == "Dr. Test Doctor"
        print("✅ Item creation and field access working")
        return True
    except Exception as e:
        print(f"❌ Item creation error: {e}")
        return False

def test_pipelines():
    """Test data processing pipelines"""
    try:
        from practo_scraper.items import DoctorItem
        from practo_scraper.pipelines import CleaningPipeline
        
        # Create test item
        item = DoctorItem()
        item['name'] = "  Dr. Test Doctor  "
        item['consultation_fee'] = "₹500"
        item['year_of_experience'] = "5 years"
        item['dp_score'] = "4.5"
        
        # Test cleaning pipeline
        pipeline = CleaningPipeline()
        cleaned_item = pipeline.process_item(item, None)
        
        assert cleaned_item['name'] == "Dr. Test Doctor"
        print("✅ Pipeline processing working")
        return True
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return False

def test_spider_configuration():
    """Test spider configuration"""
    try:
        from practo_scraper.spiders.practo_doctors_simple import PractoDoctorsSimpleSpider
        
        spider = PractoDoctorsSimpleSpider()
        assert spider.name == "practo_doctors_simple"
        assert len(spider.cities) > 0
        assert len(spider.specialities) > 0
        
        print("✅ Spider configuration working")
        return True
    except Exception as e:
        print(f"❌ Spider configuration error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing improved web scraping implementation...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_item_creation,
        test_pipelines,
        test_spider_configuration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Tests completed: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The scraping implementation is ready to use.")
        print("\\nTo run the scraper:")
        print("  python run_scraper.py --limit=5  # Test with 5 doctors")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)