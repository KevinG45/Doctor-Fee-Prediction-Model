#!/usr/bin/env python3
"""
Simple test to check if we can access Practo without browser automation
"""

import requests
import time
from urllib.parse import quote
import re
from bs4 import BeautifulSoup

def test_simple_request():
    """Test a simple HTTP request to Practo"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Test URL for Dentists in Bangalore
    speciality = "Dentist"
    city = "Bangalore"
    search_query = quote(f'[{{"word":"{speciality}","autocompleted":true,"category":"subspeciality"}}]')
    url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}"
    
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)}")
        
        if response.status_code == 200:
            # Check content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for doctor links
            doctor_links = soup.find_all('a', href=re.compile(r'/doctor/'))
            print(f"Found {len(doctor_links)} doctor links")
            
            # Look for basic content indicators
            title = soup.find('title')
            if title:
                print(f"Page Title: {title.get_text().strip()}")
            
            # Check if we got blocked
            if 'blocked' in response.text.lower() or 'captcha' in response.text.lower():
                print("❌ Appears to be blocked or requires captcha")
                return False
            
            # Check if we got valid content
            if 'practo' in response.text.lower() and ('doctor' in response.text.lower() or 'physician' in response.text.lower()):
                print("✅ Got valid Practo content")
                
                # Show a sample of doctor links
                for i, link in enumerate(doctor_links[:3]):
                    href = link.get('href', '')
                    if href:
                        print(f"  Sample doctor link {i+1}: {href}")
                
                return True
            else:
                print("❌ Content doesn't look like Practo doctor listings")
                return False
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_doctor_profile():
    """Test accessing a doctor profile page directly"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.practo.com/',
    }
    
    # Try a known doctor profile format
    profile_url = "https://www.practo.com/bangalore/doctor/dr-test-dentist"
    
    print(f"\nTesting doctor profile access: {profile_url}")
    
    try:
        response = requests.get(profile_url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 404]:  # 404 is OK for test URL
            print("✅ Can access doctor profile pages")
            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Profile request failed: {e}")
        return False

def main():
    print("=== Simple Practo Access Test ===")
    print("Testing if we can access Practo without browser automation...\n")
    
    # Test 1: Basic search page access
    search_success = test_simple_request()
    
    # Wait a bit to be polite
    time.sleep(2)
    
    # Test 2: Doctor profile access
    profile_success = test_doctor_profile()
    
    print(f"\n=== Results ===")
    print(f"Search page access: {'✅ SUCCESS' if search_success else '❌ FAILED'}")
    print(f"Profile page access: {'✅ SUCCESS' if profile_success else '❌ FAILED'}")
    
    if search_success and profile_success:
        print("\n🎉 Basic HTTP access works! We can create a non-browser scraper.")
        print("Next step: Fix the Scrapy spider to work without Playwright")
    elif search_success:
        print("\n⚠️  Search works but profiles might need different approach")
    else:
        print("\n❌ HTTP access blocked. Browser automation may be required.")
        print("Alternative: Try different headers, proxy, or request timing")

if __name__ == "__main__":
    main()