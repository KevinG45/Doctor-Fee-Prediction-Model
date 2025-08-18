#!/usr/bin/env python3
"""
Test script to validate the improved location cleaning pipeline
"""

import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'practo_scraper'))

def test_location_cleaning():
    """Test the new location cleaning functionality"""
    
    try:
        from practo_scraper.items import DoctorItem
        from practo_scraper.pipelines import CleaningPipeline
        
        print("=== Testing Location Cleaning Pipeline ===")
        
        pipeline = CleaningPipeline()
        
        # Test cases
        test_cases = [
            ("a,abbr,acronym,address,applet,article,aside,audio,b,big,blockquote,body,canvas,caption,center,cite,c", ""),
            ("New Thippasandra", "New Thippasandra"),
            ("Koramangala", "Koramangala"),
            ("JP Nagar", "JP Nagar"),
            ("div,span,p,a,b,i", ""),
            ("Whitefield", "Whitefield"),
            ("", ""),
            ("   ", ""),
            ("Jayanagar 9 Block", "Jayanagar 9 Block"),
            ("a,b,c,d,e,f,g", ""),
            ("Some very long location that is unreasonably long and should be filtered out because it's probably not a real location name at all", "")
        ]
        
        print("\nTesting location cleaning:")
        passed = 0
        total = len(test_cases)
        
        for input_location, expected in test_cases:
            result = pipeline.clean_location(input_location)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            print(f"  Input: '{input_location[:50]}{'...' if len(input_location) > 50 else ''}'")
            print(f"  Expected: '{expected}' | Got: '{result}' | {status}")
            
            if result == expected:
                passed += 1
            print()
        
        print(f"Location cleaning tests: {passed}/{total} passed")
        
        # Test full pipeline processing
        print("\nTesting full pipeline integration:")
        item = DoctorItem()
        item['name'] = "Dr. Test Doctor"
        item['location'] = "a,abbr,acronym,address,applet,article,aside,audio,b,big,blockquote,body,canvas,caption,center,cite,c"
        item['consultation_fee'] = "500"
        
        processed_item = pipeline.process_item(item, None)
        
        if processed_item['location'] == "":
            print("✅ Pipeline integration test PASSED - garbage location filtered out")
            return True
        else:
            print(f"❌ Pipeline integration test FAILED - got '{processed_item['location']}'")
            return False
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_location_cleaning()
    sys.exit(0 if success else 1)