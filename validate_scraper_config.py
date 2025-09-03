#!/usr/bin/env python3
"""
Validate scraper configuration without requiring network access
"""

import sys
import os
from pathlib import Path

def check_scrapy_project_structure():
    """Check if Scrapy project has proper structure"""
    print("=== Checking Scrapy Project Structure ===")
    
    required_files = [
        "practo_scraper/scrapy.cfg",
        "practo_scraper/practo_scraper/__init__.py", 
        "practo_scraper/practo_scraper/settings.py",
        "practo_scraper/practo_scraper/items.py",
        "practo_scraper/practo_scraper/pipelines.py",
        "practo_scraper/practo_scraper/spiders/__init__.py",
        "practo_scraper/practo_scraper/spiders/practo_doctors.py",
        "practo_scraper/practo_scraper/spiders/practo_doctors_fallback.py",
    ]
    
    all_good = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_good = False
    
    return all_good

def validate_spider_imports():
    """Test that spider imports work correctly"""
    print("\n=== Validating Spider Imports ===")
    
    # Add the project to Python path
    sys.path.insert(0, str(Path("practo_scraper").absolute()))
    
    try:
        # Test original spider import
        from practo_scraper.spiders.practo_doctors import PractoDoctorsSpider
        print("✅ Original spider imports correctly")
        
        # Test spider basic properties
        spider = PractoDoctorsSpider()
        print(f"   - Name: {spider.name}")
        print(f"   - Cities: {len(spider.cities)}")
        print(f"   - Specialities: {len(spider.specialities)}")
        
    except Exception as e:
        print(f"❌ Original spider import failed: {e}")
        
    try:
        # Test fallback spider import
        from practo_scraper.spiders.practo_doctors_fallback import PractoDoctorsFallbackSpider
        print("✅ Fallback spider imports correctly")
        
        # Test spider basic properties
        spider = PractoDoctorsFallbackSpider()
        print(f"   - Name: {spider.name}")
        print(f"   - Cities: {len(spider.cities)}")
        print(f"   - Specialities: {len(spider.specialities)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback spider import failed: {e}")
        return False

def validate_items_and_pipelines():
    """Test that items and pipelines import correctly"""
    print("\n=== Validating Items and Pipelines ===")
    
    sys.path.insert(0, str(Path("practo_scraper").absolute()))
    
    try:
        # Test items
        from practo_scraper.items import DoctorItem
        print("✅ DoctorItem imports correctly")
        
        item = DoctorItem()
        item['name'] = "Test Doctor"
        item['city'] = "Test City"
        print("   - Item creation works")
        
    except Exception as e:
        print(f"❌ Items import failed: {e}")
        return False
    
    try:
        # Test pipelines
        from practo_scraper.pipelines import (
            DeduplicationPipeline, 
            ValidationPipeline,
            CleaningPipeline
        )
        print("✅ Pipelines import correctly")
        
        # Test pipeline basic functionality
        dedup = DeduplicationPipeline()
        valid = ValidationPipeline() 
        clean = CleaningPipeline()
        print("   - Pipeline creation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipelines import failed: {e}")
        return False

def check_config_file():
    """Check if config file exists and is valid"""
    print("\n=== Checking Configuration ===")
    
    try:
        # Try to import config
        sys.path.insert(0, ".")
        from config import CITIES, SPECIALITIES
        
        print("✅ Config file imports correctly")
        print(f"   - Cities: {len(CITIES)} ({CITIES[:3]}...)")
        print(f"   - Specialities: {len(SPECIALITIES)} ({SPECIALITIES[:3]}...)")
        
        return True
        
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        print("   - Using fallback configuration")
        return False

def validate_url_generation():
    """Test URL generation logic"""
    print("\n=== Validating URL Generation ===")
    
    try:
        from urllib.parse import quote
        
        # Test URL generation like the spider does
        speciality = "Dentist"
        city = "Bangalore"
        
        search_query = quote(f'[{{"word":"{speciality}","autocompleted":true,"category":"subspeciality"}}]')
        base_url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}"
        
        print("✅ URL generation works")
        print(f"   - Generated URL: {base_url[:80]}...")
        
        # Test that URLs are properly encoded
        if "%22" in search_query and "%7B" in search_query:
            print("   - URL encoding is correct")
            return True
        else:
            print("   - URL encoding might have issues")
            return False
            
    except Exception as e:
        print(f"❌ URL generation failed: {e}")
        return False

def run_dry_validation():
    """Run validation without network requirements"""
    print("\n=== Running Dry Validation ===")
    
    # Test scrapy check command
    import subprocess
    
    try:
        os.chdir("practo_scraper")
        
        # Check fallback spider syntax
        result = subprocess.run([
            sys.executable, '-m', 'scrapy', 'check', 'practo_doctors_fallback'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Fallback spider passes scrapy validation")
            return True
        else:
            print(f"❌ Scrapy validation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Dry validation error: {e}")
        return False
    finally:
        os.chdir("..")

def main():
    """Main validation function"""
    print("🔍 Scraper Configuration Validator")
    print("=" * 50)
    print("This validates the scraper without requiring network access\n")
    
    tests = [
        ("Project Structure", check_scrapy_project_structure),
        ("Spider Imports", validate_spider_imports),
        ("Items and Pipelines", validate_items_and_pipelines), 
        ("Configuration", check_config_file),
        ("URL Generation", validate_url_generation),
        ("Dry Validation", run_dry_validation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED\n")
            else:
                print(f"❌ {test_name} FAILED\n")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}\n")
    
    print(f"=== Results ===")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All validations passed!")
        print("The scraper is properly configured and ready to run when network is available.")
        print("\nNext steps:")
        print("1. Ensure internet connectivity")
        print("2. Install Playwright browsers: playwright install chromium")
        print("3. Test scraping: cd practo_scraper && scrapy crawl practo_doctors_fallback -s CLOSESPIDER_ITEMCOUNT=3")
    else:
        print("⚠️ Some validations failed. Check the errors above.")
        print("The scraper may have configuration issues that need to be fixed.")

if __name__ == "__main__":
    main()